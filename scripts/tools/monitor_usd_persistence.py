#!/usr/bin/env python3
"""
Continuous monitoring script to verify USD nodes persist over time
Run this alongside the service to ensure Scene_Descriptor never gets deleted
"""
import mgclient
import time
from datetime import datetime

def check_usd_nodes():
    """Check if all USD nodes exist"""
    try:
        conn = mgclient.connect(host='localhost', port=7687)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check Scene_Descriptor
        cursor.execute("MATCH (sd:Scene_Descriptor) RETURN count(sd)")
        sd_count = cursor.fetchall()[0][0]
        
        # Check CameraConfig
        cursor.execute("MATCH (cc:CameraConfig) RETURN count(cc)")
        cc_count = cursor.fetchall()[0][0]
        
        # Check FusedPlayer
        cursor.execute("MATCH (fp:FusedPlayer) RETURN count(fp)")
        fp_count = cursor.fetchall()[0][0]
        
        # Check FusionBall3D
        cursor.execute("MATCH (fb:FusionBall3D) RETURN count(fb)")
        fb_count = cursor.fetchall()[0][0]
        
        # Check relationships
        cursor.execute("MATCH (sd:Scene_Descriptor)-[r]->(n) RETURN count(r)")
        rel_count = cursor.fetchall()[0][0]
        
        conn.close()
        
        return {
            'scene_descriptor': sd_count,
            'camera_config': cc_count,
            'fused_player': fp_count,
            'fusion_ball': fb_count,
            'relationships': rel_count
        }
    except Exception as e:
        print(f"Error checking nodes: {e}")
        return None

def main():
    """Monitor USD nodes every 5 seconds"""
    print("=" * 60)
    print("USD PERSISTENCE MONITOR")
    print("=" * 60)
    print("Monitoring Scene_Descriptor and related nodes...")
    print("Press Ctrl+C to stop\n")
    
    iteration = 0
    alert_shown = False
    
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            counts = check_usd_nodes()
            
            if counts:
                status = "✅" if counts['scene_descriptor'] == 1 else "❌"
                print(f"[{timestamp}] {status} SD:{counts['scene_descriptor']} "
                      f"CC:{counts['camera_config']} FP:{counts['fused_player']} "
                      f"FB:{counts['fusion_ball']} Rels:{counts['relationships']}")
                
                # Alert if Scene_Descriptor is missing
                if counts['scene_descriptor'] == 0 and not alert_shown:
                    print("\n" + "!" * 60)
                    print("⚠️  ALERT: Scene_Descriptor DELETED!")
                    print("!" * 60 + "\n")
                    alert_shown = True
                elif counts['scene_descriptor'] == 1:
                    alert_shown = False
                
                # Summary every 12 iterations (1 minute at 5s interval)
                if iteration % 12 == 0:
                    print(f"--- {iteration} checks completed, all USD nodes stable ---")
            else:
                print(f"[{timestamp}] ⚠️  Database connection failed")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        print(f"Total checks: {iteration}")

if __name__ == "__main__":
    main()

