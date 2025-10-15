#!/usr/bin/env python3
"""
Quick script to check USD nodes in Memgraph
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import mgclient

try:
    conn = mgclient.connect(host='localhost', port=7687)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("=" * 60)
    print("USD NODES CHECK")
    print("=" * 60)
    
    # Check Scene_Descriptor
    print("\n1. Scene_Descriptor nodes:")
    cursor.execute("MATCH (sd:Scene_Descriptor) RETURN sd")
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"   Found: {row[0]}")
    else:
        print("   ❌ No Scene_Descriptor nodes found")
    
    # Check CameraConfig
    print("\n2. CameraConfig nodes:")
    cursor.execute("MATCH (cc:CameraConfig) RETURN cc.cameraID, cc.role, cc.status ORDER BY cc.cameraID")
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"   {row[0]}: role={row[1]}, status={row[2]}")
    else:
        print("   ❌ No CameraConfig nodes found")
    
    # Check FusedPlayer
    print("\n3. FusedPlayer nodes:")
    cursor.execute("MATCH (fp:FusedPlayer) RETURN count(fp)")
    results = cursor.fetchall()
    count = results[0][0] if results else 0
    print(f"   Found {count} FusedPlayer nodes")
    if count > 0:
        cursor.execute("MATCH (fp:FusedPlayer) RETURN fp.id, fp.x, fp.y, fp.status ORDER BY fp.id LIMIT 5")
        results = cursor.fetchall()
        print("   Sample (first 5):")
        for row in results:
            print(f"      Player {row[0]}: x={row[1]}, y={row[2]}, status={row[3]}")
    
    # Check FusionBall3D
    print("\n4. FusionBall3D nodes:")
    cursor.execute("MATCH (fb:FusionBall3D) RETURN fb.id, fb.position_world, fb.status")
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"   Ball {row[0]}: position={row[1]}, status={row[2]}")
    else:
        print("   ❌ No FusionBall3D nodes found")
    
    # Check relationships
    print("\n5. Relationships:")
    cursor.execute("MATCH (sd:Scene_Descriptor)-[r]->(n) RETURN type(r), labels(n), count(*)")
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"   Scene_Descriptor -[{row[0]}]-> {row[1]}: {row[2]} nodes")
    else:
        print("   ❌ No relationships from Scene_Descriptor found")
    
    print("\n" + "=" * 60)
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

