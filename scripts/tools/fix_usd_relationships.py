#!/usr/bin/env python3
"""
Script to fix USD relationships - connect all unconnected FusedPlayer and FusionBall3D nodes to Scene_Descriptor
"""
import mgclient

try:
    conn = mgclient.connect(host='localhost', port=7687)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("=" * 60)
    print("FIXING USD RELATIONSHIPS")
    print("=" * 60)
    
    # Check if Scene_Descriptor exists
    print("\n1. Checking Scene_Descriptor...")
    cursor.execute("MATCH (sd:Scene_Descriptor) RETURN count(sd)")
    result = cursor.fetchall()
    sd_count = result[0][0] if result and result[0] else 0
    
    if sd_count == 0:
        print("   ❌ Scene_Descriptor not found! Run init_usd_scene.py first")
        exit(1)
    else:
        print(f"   ✅ Scene_Descriptor exists")
    
    # Connect FusedPlayer nodes
    print("\n2. Connecting FusedPlayer nodes...")
    cursor.execute("""
        MATCH (sd:Scene_Descriptor)
        MATCH (fp:FusedPlayer)
        WHERE NOT (sd)-[:HAS_PLAYER]->(fp)
        MERGE (sd)-[:HAS_PLAYER]->(fp)
        RETURN count(fp)
    """)
    result = cursor.fetchall()
    player_count = result[0][0] if result and result[0] else 0
    print(f"   ✅ Connected {player_count} FusedPlayer nodes")
    
    # Connect FusionBall3D node
    print("\n3. Connecting FusionBall3D node...")
    cursor.execute("""
        MATCH (sd:Scene_Descriptor)
        MATCH (fb:FusionBall3D)
        WHERE NOT (sd)-[:HAS_BALL]->(fb)
        MERGE (sd)-[:HAS_BALL]->(fb)
        RETURN count(fb)
    """)
    result = cursor.fetchall()
    ball_count = result[0][0] if result and result[0] else 0
    print(f"   ✅ Connected {ball_count} FusionBall3D nodes")
    
    # Verify relationships
    print("\n4. Verifying relationships...")
    cursor.execute("""
        MATCH (sd:Scene_Descriptor)-[r]->(n) 
        WITH type(r) as rel_type, labels(n)[0] as node_label
        RETURN rel_type, node_label, count(*) 
        ORDER BY rel_type
    """)
    results = cursor.fetchall()
    total_rels = 0
    for row in results:
        print(f"   {row[0]} → {row[1]}: {row[2]} nodes")
        total_rels += row[2]
    
    print(f"\n   Total relationships: {total_rels}")
    expected = 6 + 25 + 1  # 6 cameras + 25 players + 1 ball
    if total_rels >= expected:
        print(f"   ✅ All expected relationships created ({total_rels}/{expected})")
    else:
        print(f"   ⚠️  Some relationships missing ({total_rels}/{expected})")
    
    print("\n" + "=" * 60)
    print("✅ RELATIONSHIP FIXING COMPLETE!")
    print("=" * 60)
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

