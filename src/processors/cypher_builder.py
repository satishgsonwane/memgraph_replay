import orjson
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from src.core.interfaces import CacheInterface, MetricsInterface
from src.core.config import (
    PTZ_DEFAULTS, 
    PLAYER_DEFAULTS, 
    BALL_DEFAULTS,
    CAM_PARAMS_DEFAULTS,
    FUSION_BALL_3D_DEFAULTS,
    FUSED_PLAYER_DEFAULTS,
    CAMERA_CONFIG_DEFAULTS,
    INTENT_DEFAULTS,
    logger
)
import uuid

# ---------------------------------------------------
# Message Processing Component
# ---------------------------------------------------

class CypherBuilder:
    """Handles conversion of NATS messages to Cypher batch data with one-node-per-detection storage"""
    
    def __init__(self, cache: CacheInterface, metrics: MetricsInterface):
        self.cache = cache
        self.metrics = metrics
        self.system_timestamp = None  # Will be set per batch

    def to_json_str(self, data: Any) -> str:
        """Ultra-fast JSON serialization for maximum performance"""
        return orjson.dumps(data, option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NAIVE_UTC).decode('utf-8')
    
    def generate_time_based_uuid(self, current_tick: int) -> str:
        """Generate a time-based UUID that can be compared lexicographically for cleanup"""
        # Use current tick as the first 8 characters of the UUID
        # This ensures lexicographic ordering matches temporal ordering
        tick_hex = f"{current_tick:08x}"
        # Generate a random suffix to ensure uniqueness
        random_suffix = str(uuid.uuid4())[8:]  # Remove first 8 chars and use the rest
        return f"{tick_hex}-{random_suffix}"

    def ensure_properties(self, data: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Ultra-optimized property handling for sub-10ms P95 latency"""
        # Single-pass dict comprehension for maximum speed
        return {
            k: data.get(k, v) if data.get(k) is not None else v
            for k, v in defaults.items()
        }

    def set_system_timestamp(self, timestamp: str) -> None:
        """Set system timestamp for current batch processing"""
        self.system_timestamp = timestamp

    def get_timestamp_for_entity(self, data: Dict[str, Any], fallback_to_system: bool = True) -> str:
        """Get timestamp from message or use system timestamp"""
        # Try to get timestamp from message first
        if "timestamp" in data:
            return data["timestamp"]  # ISO 8601 UTC from NATS
        elif "last_updated" in data:
            # Convert Unix timestamp to ISO 8601
            unix_time = data["last_updated"]
            dt = datetime.fromtimestamp(unix_time, tz=timezone.utc)
            return dt.isoformat().replace('+00:00', 'Z')
        elif fallback_to_system and self.system_timestamp:
            return self.system_timestamp  # System-generated timestamp
        else:
            # Fallback to current system time
            return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    def build_queries(self, topic: str, data: Dict[str, Any], current_tick: int) -> Any:
        """Convert NATS message to Cypher batch data with time-based TTL support"""
        if current_tick is None:
            logger.warning(f"[Skip] current_tick is None for topic {topic}. Skipping.")
            return None

        # Get appropriate timestamp for this message
        timestamp = self.get_timestamp_for_entity(data)

        try:
            if topic.startswith("tickperframe"):
                # Direct access instead of TickPerFrameModel(**data)
                count = data.get("count", 0)
                # Pre-create Frame node with system timestamp
                return ("Frame", {
                    "tickID": count,
                    "timestamp": timestamp  # System timestamp
                })

            elif topic.startswith("ptzinfo."):
                cameraID = topic.split(".")[1]

                if not self.cache.has_changed(topic, data):
                    return None
                
                # Direct property handling instead of model.model_dump(exclude_none=True)
                props = self.ensure_properties(data, PTZ_DEFAULTS)
                ptz_row = {
                    "stateID": f"{cameraID}_{current_tick}",
                    "cameraID": cameraID,
                    "tickID": current_tick,
                    "timestamp": timestamp,  # System timestamp
                }
                ptz_row.update(props)
                
                # Return both PTZState and Camera pre-creation
                return [
                    ("Camera", {
                        "cameraID": cameraID, 
                        "tickID": current_tick,
                        "timestamp": timestamp,  # System timestamp
                        "last_active_timestamp": timestamp  # For cleanup
                    }),
                    ("PTZState", ptz_row)
                ]

            elif topic.startswith("all_tracks."):
                cameraID = topic.split(".")[1]
                
                # Get balls, players, PTZ data, and cam_params
                balls = data.get("balls", [])
                players = data.get("players", [])
                ptz_data = data.get("PTZ", {})
                cam_params_data = data.get("cam_params", {})
                
                # Pre-allocate result list
                rows = []
                
                # Create Frame node first (needed for relationships)
                rows.append(("Frame", {
                    "tickID": current_tick,
                    "timestamp": timestamp
                }))
                
                # Create Camera node
                rows.append(("Camera", {
                    "cameraID": cameraID, 
                    "tickID": current_tick,
                    "timestamp": timestamp,
                    "last_active_timestamp": timestamp
                }))
                
                # Process PTZ data if present
                if ptz_data:
                    ptz_props = self.ensure_properties(ptz_data, PTZ_DEFAULTS)
                    rows.append(("PTZState", {
                        "stateID": f"{cameraID}_{current_tick}",
                        "cameraID": cameraID,
                        "tickID": current_tick,
                        "timestamp": timestamp,
                        **ptz_props
                    }))
                
                # Process cam_params data if present
                if cam_params_data:
                    cam_params_props = self.ensure_properties(cam_params_data, CAM_PARAMS_DEFAULTS)
                    rows.append(("CamParams", {
                        "paramsID": f"{cameraID}_{current_tick}",
                        "cameraID": cameraID,
                        "tickID": current_tick,
                        "timestamp": timestamp,
                        **cam_params_props
                    }))
                
                # Update CameraConfig with gimbal position and camera parameters for USD schema
                if ptz_data or cam_params_data:
                    # Build gimbal position from PTZ data
                    gimbal_position = {
                        "pan": ptz_data.get("panposition") if ptz_data else None,
                        "tilt": ptz_data.get("tiltposition") if ptz_data else None,
                        "zoom": ptz_data.get("zoomposition") if ptz_data else None
                    }
                    
                    # Build camera parameters from cam_params
                    camera_parameters = {
                        "intrinsic": cam_params_data.get("intrinsic") if cam_params_data else None,
                        "rotation": cam_params_data.get("rotation") if cam_params_data else None,
                        "translation": cam_params_data.get("translation") if cam_params_data else None
                    }
                    
                    # Add CameraConfig update row
                    rows.append(("CameraConfigUpdate", {
                        "cameraID": cameraID,
                        "gimbal_position": gimbal_position,
                        "camera_parameters": camera_parameters,
                        "timestamp": timestamp
                    }))
                
                # Process balls with array-based approach
                for idx, ball in enumerate(balls):
                    props = self.ensure_properties(ball, BALL_DEFAULTS)
                    track_id = props.get('track_id') or props.get('id')  # Handle both 'track_id' and 'id' fields
                    if track_id is not None:
                        row = {
                            "track_id": track_id,
                            "cameraID": cameraID,
                            "current_tick": current_tick,
                            "timestamp": timestamp,
                            **props
                        }
                        rows.append(("BallTrack", row))
                
                # Process players with array-based approach  
                for idx, player in enumerate(players):
                    props = self.ensure_properties(player, PLAYER_DEFAULTS)
                    track_id = props.get('track_id')
                    if track_id is not None:
                        row = {
                            "track_id": track_id,
                            "cameraID": cameraID,
                            "current_tick": current_tick,
                            "timestamp": timestamp,
                            **props
                        }
                        rows.append(("PlayerTrack", row))
                
                return rows

            elif topic.startswith("fusion.ball_3d"):
                # Fusion ball 3D is a singleton - no tickID needed (MERGE pattern)
                props = self.ensure_properties(data, FUSION_BALL_3D_DEFAULTS)
                return ("FusionBall3D", {
                    "timestamp": timestamp,
                    **props
                })

            elif topic.startswith("fused_players"):
                # Fused players array - MERGE pattern for each player (latest state only)
                # Data is expected to be a list of player objects
                if not isinstance(data, list):
                    logger.warning(f"fused_players data is not a list: {type(data)}")
                    return None
                
                rows = []
                for player in data:
                    props = self.ensure_properties(player, FUSED_PLAYER_DEFAULTS)
                    player_id = props.get('id')
                    if player_id is not None:
                        row = {
                            "id": player_id,
                            "x": props.get('x'),
                            "y": props.get('y'),
                            "z": props.get('z', 0.0),
                            "vel_x": props.get('vel_x'),
                            "vel_y": props.get('vel_y'),
                            "status": props.get('status'),
                            "category": props.get('category'),
                            "team": props.get('team'),
                            "timestamp": timestamp
                        }
                        rows.append(("FusedPlayer", row))
                
                return rows if rows else None

            elif topic.startswith("intents.processed"):
                # Intent data - MERGE pattern (one intent per camera, persistent)
                props = self.ensure_properties(data, INTENT_DEFAULTS)
                camera_id = props.get('camera_id')
                
                if camera_id is None:
                    logger.warning(f"Intent message missing camera_id: {data}")
                    return None
                
                # Convert nested dicts to JSON strings for Memgraph storage
                payload_json = self.to_json_str(props.get('payload')) if props.get('payload') is not None else None
                rule_definition_json = self.to_json_str(props.get('rule_definition')) if props.get('rule_definition') is not None else None
                
                return ("Intent", {
                    "cameraID": camera_id,
                    "status": props.get('status'),
                    "intent_id": props.get('intent_id'),
                    "intent_type": props.get('intent_type'),
                    "resolved_ttl_ms": props.get('resolved_ttl_ms'),
                    "payload": payload_json,
                    "rule_definition": rule_definition_json,
                    "reason": props.get('reason'),
                    "timestamp": timestamp
                })

            else:
                # Skip all other topics
                logger.debug(f"Skipping unsupported topic: {topic}")
                return None

        except KeyError as ke:
            logger.error(f"Missing required field for topic {topic}: {ke}")
            return None
        except Exception as e:
            logger.error(f"Error parsing topic {topic}: {e}")
            return None

    def process_message(self, topic: str, data: Dict[str, Any], current_tick: int) -> Any:
        """Alias for build_queries to maintain test compatibility"""
        return self.build_queries(topic, data, current_tick) 