"""
Scene Initializer Module

Handles one-time initialization of the USD-based Scene_Descriptor graph structure.
This includes creating the singleton Scene_Descriptor node and 6 CameraConfig nodes.
"""

from typing import Dict, Any
from src.core.interfaces import DatabaseInterface
from src.core.config import logger
import orjson


class SceneInitializer:
    """Handles initialization of Scene_Descriptor and related USD nodes"""
    
    def __init__(self, database: DatabaseInterface):
        self.database = database
        self._initialized = False
    
    async def initialize_scene_descriptor(self, venue_id: str, pitch_markers: Dict[str, tuple]) -> None:
        """
        Create or update the singleton Scene_Descriptor node with venue metadata.
        
        Args:
            venue_id: Venue identifier (e.g., 'ozsports')
            pitch_markers: Dictionary of pitch landmark coordinates
        """
        try:
            # Convert pitch_markers tuples to lists and handle numpy types for JSON serialization
            # Need to convert numpy types to native Python types
            import numpy as np
            pitch_markers_clean = {}
            for key, value in pitch_markers.items():
                if isinstance(value, tuple):
                    # Convert tuple of possibly numpy floats to list of Python floats
                    pitch_markers_clean[key] = [float(v) if isinstance(v, (np.floating, np.integer)) else v for v in value]
                else:
                    pitch_markers_clean[key] = float(value) if isinstance(value, (np.floating, np.integer)) else value
            
            pitch_markers_json = orjson.dumps(pitch_markers_clean).decode('utf-8')
            
            logger.info(f"Initializing Scene_Descriptor for venue: {venue_id}")
            logger.debug(f"Pitch markers JSON length: {len(pitch_markers_json)} characters")
            
            query = """
            MERGE (sd:Scene_Descriptor {venue_id: $venue_id})
            SET sd.units = $units,
                sd.up_axis = $up_axis,
                sd.origin = $origin,
                sd.handedness = $handedness,
                sd.version = $version,
                sd.pitch_markers = $pitch_markers
            RETURN sd
            """
            
            params = {
                'venue_id': venue_id,
                'units': 'meters',
                'up_axis': 'Z',
                'origin': 'PITCH_TOP_LEFT',
                'handedness': 'RIGHT',
                'version': '1.0',
                'pitch_markers': pitch_markers_json
            }
            
            result = await self.database.execute_query(query, params)
            logger.info(f"✅ Scene_Descriptor initialized for venue: {venue_id}, result: {result}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Scene_Descriptor: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def initialize_camera_configs(self, camera_configs: list, venue_id: str) -> None:
        """
        Create or update CameraConfig nodes and link them to Scene_Descriptor.
        
        Args:
            camera_configs: List of camera configuration dicts
            venue_id: Venue identifier to link cameras to Scene_Descriptor
        """
        if len(camera_configs) != 6:
            logger.warning(f"Expected 6 camera configs, got {len(camera_configs)}")
        
        try:
            logger.info(f"Initializing {len(camera_configs)} CameraConfig nodes...")
            
            for config in camera_configs:
                # Extract camera data with proper formatting
                camera_id = config.get('cameraID')
                
                # Convert nested dicts to JSON strings for Memgraph
                gimbal_json = orjson.dumps(config.get('gimbal_position', {})).decode('utf-8')
                params_json = orjson.dumps(config.get('camera_parameters', {})).decode('utf-8')
                
                logger.debug(f"Processing {camera_id}: role={config.get('role')}, status={config.get('status')}")
                
                query = """
                MERGE (cc:CameraConfig {cameraID: $cameraID})
                SET cc.role = $role,
                    cc.status = $status,
                    cc.operation_mode = $operation_mode,
                    cc.zoom_mode = $zoom_mode,
                    cc.pan_range = $pan_range,
                    cc.tilt_range = $tilt_range,
                    cc.zoom_range = $zoom_range,
                    cc.camerapos = $camerapos,
                    cc.venue = $venue,
                    cc.gimbal_position = $gimbal_position,
                    cc.camera_parameters = $camera_parameters
                WITH cc
                MATCH (sd:Scene_Descriptor {venue_id: $venue})
                MERGE (sd)-[:HAS_CAMERA]->(cc)
                RETURN cc
                """
                
                params = {
                    'cameraID': camera_id,
                    'role': config.get('role'),
                    'status': config.get('status', 'ACTIVE').upper(),
                    'operation_mode': config.get('operation_mode'),
                    'zoom_mode': config.get('zoom_mode'),
                    'pan_range': config.get('pan_range'),
                    'tilt_range': config.get('tilt_range'),
                    'zoom_range': config.get('zoom_range'),
                    'camerapos': config.get('camerapos'),
                    'venue': venue_id,
                    'gimbal_position': gimbal_json,
                    'camera_parameters': params_json
                }
                
                result = await self.database.execute_query(query, params)
                logger.debug(f"✅ Initialized CameraConfig: {camera_id} with role {config.get('role')}, result: {result}")
            
            logger.info(f"✅ Initialized {len(camera_configs)} CameraConfig nodes")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize CameraConfig nodes: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def initialize_all(self) -> None:
        """
        Initialize complete Scene_Descriptor structure with venue, pitch markers, and cameras.
        This should be called once on service startup.
        """
        try:
            # Import here to avoid circular dependencies
            try:
                from gen_pitch_data import get_pitch_markers, get_camera_configs, get_venue_id
            except ImportError:
                # Fallback to standalone version if oz_core dependency is missing
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent.parent.parent / "data" / "config"))
                from gen_pitch_data_standalone import get_pitch_markers, get_camera_configs, get_venue_id
            
            logger.info("🏟️  Initializing USD Scene_Descriptor structure...")
            
            # Get data from pitch_data module
            venue_id = get_venue_id()
            pitch_markers = get_pitch_markers()
            camera_configs = get_camera_configs()
            
            # Initialize Scene_Descriptor first
            await self.initialize_scene_descriptor(venue_id, pitch_markers)
            
            # Then initialize camera configs
            await self.initialize_camera_configs(camera_configs, venue_id)
            
            logger.info("✅ USD Scene_Descriptor structure fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize USD scene structure: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't raise - allow service to continue even if scene init fails

