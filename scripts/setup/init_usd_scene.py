#!/usr/bin/env python3
"""
Standalone script to initialize USD Scene_Descriptor structure
Run this to manually initialize the Scene_Descriptor and CameraConfig nodes
"""
import asyncio
import sys
from pathlib import Path

# Add paths
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.repository import Memgraph
from src.utils.scene_initializer import SceneInitializer
from src.core.config import logger

async def main():
    """Initialize USD scene structure"""
    try:
        logger.info("=" * 60)
        logger.info("USD SCENE INITIALIZATION")
        logger.info("=" * 60)
        
        # Connect to database
        logger.info("\n1. Connecting to Memgraph...")
        db = Memgraph(host='localhost', port=7687)
        logger.info("✅ Connected to Memgraph")
        
        # Create initializer
        logger.info("\n2. Creating SceneInitializer...")
        initializer = SceneInitializer(db)
        
        # Run initialization
        logger.info("\n3. Running initialization...")
        await initializer.initialize_all()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ INITIALIZATION COMPLETE!")
        logger.info("=" * 60)
        
        # Verify results
        logger.info("\n4. Verifying results...")
        result = await db.execute_query("MATCH (sd:Scene_Descriptor) RETURN count(sd)")
        scene_count = result[0][0] if result and result[0] else 0
        logger.info(f"   Scene_Descriptor nodes: {scene_count}")
        
        result = await db.execute_query("MATCH (cc:CameraConfig) RETURN count(cc)")
        camera_count = result[0][0] if result and result[0] else 0
        logger.info(f"   CameraConfig nodes: {camera_count}")
        
        result = await db.execute_query("MATCH (sd:Scene_Descriptor)-[r:HAS_CAMERA]->(cc:CameraConfig) RETURN count(r)")
        rel_count = result[0][0] if result and result[0] else 0
        logger.info(f"   HAS_CAMERA relationships: {rel_count}")
        
        if scene_count == 1 and camera_count == 6 and rel_count == 6:
            logger.info("\n✅ All checks passed!")
        else:
            logger.warning("\n⚠️  Some nodes/relationships missing!")
        
        await db.close()
        
    except Exception as e:
        logger.error(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

