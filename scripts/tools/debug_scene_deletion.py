#!/usr/bin/env python3
"""
Advanced debugging script to identify when and why Scene_Descriptor gets deleted
This monitors Memgraph and attempts to detect the exact moment of deletion
"""
import mgclient
import time
from datetime import datetime
import sys

def get_scene_state():
    """Get current state of Scene_Descriptor and related info"""
    try:
        conn = mgclient.connect(host='localhost', port=7687)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check Scene_Descriptor
        cursor.execute("MATCH (sd:Scene_Descriptor) RETURN count(sd), id(sd)")
        result = cursor.fetchall()
        sd_count = result[0][0] if result and result[0] else 0
        sd_id = result[0][1] if result and result[0] and sd_count > 0 else None
        
        # Check relationships
        cursor.execute("MATCH (sd:Scene_Descriptor)-[r]->() RETURN count(r)")
        rel_count = cursor.fetchall()[0][0] if cursor.fetchall() else 0
        
        # Check total node count for correlation
        cursor.execute("MATCH (n) RETURN count(n)")
        total_nodes = cursor.fetchall()[0][0]
        
        # Check Frame count (cleanup target)
        cursor.execute("MATCH (f:Frame) RETURN count(f)")
        frame_count = cursor.fetchall()[0][0]
        
        conn.close()
        
        return {
            'exists': sd_count > 0,
            'id': sd_id,
            'relationships': rel_count,
            'total_nodes': total_nodes,
            'frames': frame_count,
            'timestamp': datetime.now()
        }
    except Exception as e:
        return {
            'exists': False,
            'error': str(e),
            'timestamp': datetime.now()
        }

def main():
    print("=" * 80)
    print("SCENE_DESCRIPTOR DELETION DEBUGGER")
    print("=" * 80)
    print("Monitoring Scene_Descriptor every second...")
    print("This will help identify WHEN it gets deleted")
    print("Press Ctrl+C to stop\n")
    
    last_state = None
    deletion_detected = False
    check_count = 0
    
    try:
        while True:
            check_count += 1
            state = get_scene_state()
            timestamp = state['timestamp'].strftime("%H:%M:%S")
            
            if 'error' in state:
                print(f"[{timestamp}] ⚠️  Database error: {state['error']}")
                time.sleep(1)
                continue
            
            # Check for deletion event
            if last_state and last_state['exists'] and not state['exists']:
                print("\n" + "!" * 80)
                print(f"❌ DELETION DETECTED AT {timestamp}!")
                print("!" * 80)
                print(f"Scene_Descriptor existed {check_count-1} checks ago")
                print(f"Last known ID: {last_state.get('id')}")
                print(f"Last relationships: {last_state.get('relationships')}")
                print(f"Total nodes before: {last_state.get('total_nodes')}")
                print(f"Total nodes after: {state.get('total_nodes')}")
                print(f"Nodes deleted: {last_state.get('total_nodes', 0) - state.get('total_nodes', 0)}")
                print(f"Frames before: {last_state.get('frames')}")
                print(f"Frames after: {state.get('frames')}")
                print("!" * 80 + "\n")
                deletion_detected = True
            
            # Check for recreation event
            if last_state and not last_state['exists'] and state['exists']:
                print(f"\n[{timestamp}] ✅ Scene_Descriptor RECREATED (ID: {state.get('id')})")
                print(f"   Relationships restored: {state.get('relationships')}\n")
                deletion_detected = False
            
            # Normal monitoring
            if state['exists']:
                status = "✅"
                node_info = f"ID:{state.get('id')} Rels:{state.get('relationships')}"
            else:
                status = "❌"
                node_info = "MISSING"
            
            print(f"[{timestamp}] Check #{check_count:04d} {status} {node_info} "
                  f"| Nodes:{state.get('total_nodes'):5d} Frames:{state.get('frames'):4d}", 
                  end='\r' if not deletion_detected else '\n')
            
            if deletion_detected:
                print()  # Add newline after deletion event
            
            last_state = state
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\nMonitoring stopped after {check_count} checks")
        if last_state and last_state['exists']:
            print(f"✅ Scene_Descriptor still exists")
        else:
            print(f"❌ Scene_Descriptor is MISSING")
        sys.exit(0)

if __name__ == "__main__":
    main()

