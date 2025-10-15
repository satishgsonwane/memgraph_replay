"""Make changes to the file for mock data generation only (not runtime validation)"""


from pydantic import BaseModel, Field, RootModel
from typing import List, Optional, Dict, Any
from enum import Enum

# ENUM for object category
class ObjectCategory(str, Enum):
    PLAYER = 'player'
    REFEREE = 'referee'

# Tick counter model. Checked with the JSON schema and it's correct.
class TickPerFrameModel(BaseModel):
    count: int
    framerate: Optional[float]

# Detection ball model. Checked with the JSON schema and it's correct.
class BallTrackModel(BaseModel):
    world_x: float
    world_y: float
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    transform_PAN: Optional[float] = None
    transform_TILT: Optional[float] = None
    confidence: Optional[float] = None  # Alternative field name used in all_tracks messages
    dist: Optional[float] = None
    phi: Optional[float] = None
    track_id: Optional[int] = None  # Alternative field name used in all_tracks messages
    velocity: Optional[float] = None
    movement_score: Optional[float] = None
    velocity_direction: Optional[float] = None
    velocity_x: Optional[float] = None
    velocity_y: Optional[float] = None
    id_score: Optional[float] = None # only present in best_track
    dist_score: Optional[float] = None # only present in best_track
    is_best: Optional[bool] = None  # only present in all_tracks
    # 3D ray casting properties for ball detection
    ray_origin: Optional[List[float]] = None  # List[float] with length 3 [x, y, z]
    ray_world_space_dir: Optional[List[float]] = None  # List[float] with length 3 [x, y, z]

# Detection player/referee model. Checked with the JSON schema and it's correct.
class DetectionModel(BaseModel):
    category: ObjectCategory
    track_id: Optional[int]
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    confidence: float
    world_x: Optional[float] = None
    world_y: Optional[float] = None
    transform_PAN: Optional[float] = None
    transform_TILT: Optional[float] = None
    dist: Optional[float] = None
    # keypoints: Optional[Dict[str, Any]] = None
    # attributes: Optional[Dict[str, Any]] = None
    # 3D ray casting properties for player detection
    ray_origin: Optional[List[float]] = None  # List[float] with length 3 [x, y, z]
    ray_world_space_dir: Optional[List[float]] = None  # List[float] with length 3 [x, y, z]
    # vx: Optional[float] = None
    # vy: Optional[float] = None

# Best track data model. Checked with the JSON schema and it's correct.
class BestTrackModel(BaseModel):
    tickID: Optional[int] = None
    PTZ: Optional[Dict[str, str]] = None
    balls: Optional[BallTrackModel] = None  # single ball as dict
    players: Optional[List[DetectionModel]] = None
    AFFILIATION: Optional[bool] = None

    class Config:
        extra = "ignore"

# All tracks data model. Checked with the JSON schema and it's correct.
class AllTrackFrameModel(BaseModel):
    tickID: Optional[int] = None
    PTZ: Optional[Dict[str, Any]] = None  # Fixed: numeric values, not strings
    balls: Optional[List[BallTrackModel]] = None  # multiple balls as list
    players: Optional[List[DetectionModel]] = None
    AFFILIATION: Optional[bool] = None

    class Config:
        extra = "ignore"

# Fusion ball data model. Checked with the JSON schema and it's correct.
class FusionBallModel(BaseModel):
    world_x: float
    world_y: float
    average_resultant_velocity: float
    average_velocity_x: float
    average_velocity_y: float
    last_updated: Optional[float] = 0
    tickID: Optional[int] = None

# Manual override model. Checked with the JSON schema and it's correct.
class TopViewPosition(BaseModel):
    x: int
    y: int

class OverrideValueModel(BaseModel):
    side: str
    position: str
    top_view_position: TopViewPosition
    landmark_id: int

class ManualOverrideModel(BaseModel):
    tickID: Optional[int] = None
    override_type: str
    cameras: List[int]
    override_value: OverrideValueModel
    detector_config: List[Any]

class CameraCutTransition(BaseModel):
    delay: Optional[float]
    transitiontime: Optional[float]
    opacity: Optional[int]  # keep name as-is to match the JSON structure

class CameraCutEntry(BaseModel):
    id: Optional[str] = None
    playspeed: Optional[float] = None
    controlspeed: Optional[int] = None
    zorder: Optional[int] = None
    opacity: Optional[int] = None  # outer opacity
    transition: Optional[CameraCutTransition] = None
    animation: Optional[str] = None

    class Config:
        extra = "allow"  # to allow fields like 'animation' when 'id' is missing

class CameraCutsWrapper(BaseModel):
    tickID: Optional[int] = None
    cameracuts: List[CameraCutEntry]

class Viewport(BaseModel):
    inx: int
    iny: int
    inwidth: int
    inheight: int

class DigitalPTZModel(BaseModel):
    tickID: int  # required

    class Config:
        extra = "allow"  # allows top-level camera keys like "/replay2"

class PTZInfoModel(BaseModel):
    panposition: Optional[float] = None
    tiltposition: Optional[float] = None
    rollposition: Optional[float] = None
    pansetpoint: Optional[float] = None
    tiltsetpoint: Optional[float] = None
    zoomsetpoint: Optional[float] = None
    panpower: Optional[float] = None
    tiltpower: Optional[float] = None
    rollpower: Optional[float] = None
    pan: Optional[float] = None
    tilt: Optional[float] = None
    zoomspeed: Optional[float] = None
    zoomposition: Optional[float] = None
    focusposition: Optional[float] = None
    # New velocity fields from updated all_tracks message structure
    panvelocity: Optional[float] = None
    tiltvelocity: Optional[float] = None
    zoomvelocity: Optional[float] = None
    tickID: Optional[int] = None

class CaminqModel(BaseModel):
    ExposureMode: Optional[str]
    VisibilityEnhancer: Optional[str]
    VisibilityEnhancerLevel: Optional[str]
    ExposureMaxGain: Optional[str]
    ExposureMaxExposureTime: Optional[str]
    ExposureMinExposureTime: Optional[str]
    ExposureCompensation: Optional[str]
    BacklightCompensationMode: Optional[str]
    SpotlightCompensationMode: Optional[str]
    ExposureExposureTimePri: Optional[str]
    ExposureIrisPri: Optional[str]
    ExposureGain: Optional[str]
    ExposureIris: Optional[str]
    ExposureExposureTime: Optional[str]
    WhiteBalanceMode: Optional[str]
    WhiteBalanceCrGain: Optional[str]
    WhiteBalanceCbGain: Optional[str]
    ColorMatrixEnable: Optional[str]
    ColorSaturation: Optional[str]
    ColorHue: Optional[str]
    DetailLevel: Optional[str]
    GammaLevel: Optional[str]
    DigitalBrightLevel: Optional[str]
    NoiseReduction2DLevel: Optional[str]
    NoiseReduction3DLevel: Optional[str]
    FlickerReduction: Optional[str]

class CameraModeEntry(BaseModel):
    operation_mode: Optional[str] = None
    ai_focus: Optional[str] = None
    zoom_mode: Optional[str] = None
    role: Optional[str] = None

class CameraControlModeModel(RootModel):
    root: Dict[str, CameraModeEntry]

# Intent models for intents.processed NATS topic
class IntentPayload(BaseModel):
    """Intent payload structure"""
    offset_level: Optional[str] = None
    direction: Optional[str] = None

class IntentRuleDefinition(BaseModel):
    """Intent rule definition structure"""
    action: Optional[str] = None
    axis: Optional[str] = None
    default_ttl_level: Optional[str] = None

class IntentProcessed(BaseModel):
    """Model for intents.processed NATS topic"""
    status: str  # "active" or "expired"
    intent_id: str  # UUID or "superseded"
    camera_id: str  # e.g., "camera5"
    intent_type: str  # e.g., "nudge_tilt", "nudge_pan", "none", "unknown"
    resolved_ttl_ms: Optional[int] = None
    payload: Optional[IntentPayload] = None
    rule_definition: Optional[IntentRuleDefinition] = None
    reason: Optional[str] = None  # e.g., "SUPERSEDED", "TTL_EXPIRED" 