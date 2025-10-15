#!/usr/bin/env python3
"""
Standalone pitch data generator without external dependencies
This provides the same interface as gen_pitch_data.py but with hardcoded data
"""

from typing import Dict, List, Any


def get_pitch_markers() -> Dict[str, tuple]:
    """
    Get pitch landmark coordinates as a dictionary.
    
    Returns:
        Dict mapping landmark names to (x, y) tuples in meters
    """
    # Standard football pitch dimensions and landmarks
    return {
        "center_spot": (0.0, 0.0),
        "center_circle_radius": (9.15, 0.0),  # FIFA standard
        "penalty_spot_home": (-32.0, 0.0),
        "penalty_spot_away": (32.0, 0.0),
        "goal_post_home_left": (-52.5, -3.66),
        "goal_post_home_right": (-52.5, 3.66),
        "goal_post_away_left": (52.5, -3.66),
        "goal_post_away_right": (52.5, 3.66),
        "corner_home_left": (-52.5, -34.0),
        "corner_home_right": (-52.5, 34.0),
        "corner_away_left": (52.5, -34.0),
        "corner_away_right": (52.5, 34.0),
        "penalty_area_home_left": (-40.0, -20.16),
        "penalty_area_home_right": (-40.0, 20.16),
        "penalty_area_away_left": (40.0, -20.16),
        "penalty_area_away_right": (40.0, 20.16),
        "six_yard_home_left": (-46.0, -9.16),
        "six_yard_home_right": (-46.0, 9.16),
        "six_yard_away_left": (46.0, -9.16),
        "six_yard_away_right": (46.0, 9.16)
    }


def get_camera_configs() -> List[Dict[str, Any]]:
    """
    Get camera configuration data for all 6 cameras.
    
    Returns:
        List of 6 camera config dicts with role, status, ranges, position, etc.
    """
    # Standard 6-camera setup for football pitch
    configs = [
        {
            'cameraID': 'camera1',
            'role': 'main',
            'status': 'ACTIVE',
            'operation_mode': 'auto',
            'zoom_mode': 'wide',
            'pan_range': [-180.0, 180.0],
            'tilt_range': [-45.0, 45.0],
            'zoom_range': [1.0, 10.0],
            'camerapos': [0.0, 0.0, 10.0],
            'gimbal_position': {'pan': 0.0, 'tilt': 0.0, 'zoom': 1.0},
            'camera_parameters': {
                'intrinsic': [[800.0, 0.0, 640.0], [0.0, 800.0, 360.0], [0.0, 0.0, 1.0]],
                'rotation': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                'translation': [0.0, 0.0, 10.0]
            },
            'venue': 'ozsports'
        },
        {
            'cameraID': 'camera2',
            'role': 'center',
            'status': 'ACTIVE',
            'operation_mode': 'auto',
            'zoom_mode': 'wide',
            'pan_range': [-180.0, 180.0],
            'tilt_range': [-45.0, 45.0],
            'zoom_range': [1.0, 10.0],
            'camerapos': [0.0, 0.0, 15.0],
            'gimbal_position': {'pan': 0.0, 'tilt': -10.0, 'zoom': 1.5},
            'camera_parameters': {
                'intrinsic': [[800.0, 0.0, 640.0], [0.0, 800.0, 360.0], [0.0, 0.0, 1.0]],
                'rotation': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                'translation': [0.0, 0.0, 15.0]
            },
            'venue': 'ozsports'
        },
        {
            'cameraID': 'camera3',
            'role': 'l_sideline',
            'status': 'ACTIVE',
            'operation_mode': 'auto',
            'zoom_mode': 'wide',
            'pan_range': [-180.0, 180.0],
            'tilt_range': [-45.0, 45.0],
            'zoom_range': [1.0, 10.0],
            'camerapos': [-45.0, 0.0, 12.0],
            'gimbal_position': {'pan': 90.0, 'tilt': -5.0, 'zoom': 1.0},
            'camera_parameters': {
                'intrinsic': [[800.0, 0.0, 640.0], [0.0, 800.0, 360.0], [0.0, 0.0, 1.0]],
                'rotation': [[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
                'translation': [-45.0, 0.0, 12.0]
            },
            'venue': 'ozsports'
        },
        {
            'cameraID': 'camera4',
            'role': 'r_sideline',
            'status': 'ACTIVE',
            'operation_mode': 'auto',
            'zoom_mode': 'wide',
            'pan_range': [-180.0, 180.0],
            'tilt_range': [-45.0, 45.0],
            'zoom_range': [1.0, 10.0],
            'camerapos': [45.0, 0.0, 12.0],
            'gimbal_position': {'pan': -90.0, 'tilt': -5.0, 'zoom': 1.0},
            'camera_parameters': {
                'intrinsic': [[800.0, 0.0, 640.0], [0.0, 800.0, 360.0], [0.0, 0.0, 1.0]],
                'rotation': [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
                'translation': [45.0, 0.0, 12.0]
            },
            'venue': 'ozsports'
        },
        {
            'cameraID': 'camera5',
            'role': 'l_goal',
            'status': 'ACTIVE',
            'operation_mode': 'auto',
            'zoom_mode': 'closeup',
            'pan_range': [-180.0, 180.0],
            'tilt_range': [-45.0, 45.0],
            'zoom_range': [1.0, 10.0],
            'camerapos': [-52.5, 0.0, 8.0],
            'gimbal_position': {'pan': 0.0, 'tilt': 0.0, 'zoom': 2.0},
            'camera_parameters': {
                'intrinsic': [[800.0, 0.0, 640.0], [0.0, 800.0, 360.0], [0.0, 0.0, 1.0]],
                'rotation': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                'translation': [-52.5, 0.0, 8.0]
            },
            'venue': 'ozsports'
        },
        {
            'cameraID': 'camera6',
            'role': 'r_goal',
            'status': 'ACTIVE',
            'operation_mode': 'auto',
            'zoom_mode': 'closeup',
            'pan_range': [-180.0, 180.0],
            'tilt_range': [-45.0, 45.0],
            'zoom_range': [1.0, 10.0],
            'camerapos': [52.5, 0.0, 8.0],
            'gimbal_position': {'pan': 180.0, 'tilt': 0.0, 'zoom': 2.0},
            'camera_parameters': {
                'intrinsic': [[800.0, 0.0, 640.0], [0.0, 800.0, 360.0], [0.0, 0.0, 1.0]],
                'rotation': [[-1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]],
                'translation': [52.5, 0.0, 8.0]
            },
            'venue': 'ozsports'
        }
    ]
    
    return configs


def get_venue_id() -> str:
    """
    Get venue identifier.
    
    Returns:
        Venue ID string (e.g., 'ozsports')
    """
    return 'ozsports'


if __name__ == "__main__":
    # Test the functions
    print("Pitch Markers:")
    markers = get_pitch_markers()
    for name, coords in markers.items():
        print(f"  {name}: {coords}")
    
    print("\nCamera Configs:")
    configs = get_camera_configs()
    for config in configs:
        print(f"  {config['cameraID']}: {config['role']} - {config['status']}")
    
    print("\nVenue ID:")
    print(f"  {get_venue_id()}")
