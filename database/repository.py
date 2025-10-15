import mgclient
import time
import asyncio
from typing import Optional, Dict, Any, List
from src.core.interfaces import DatabaseInterface, TransactionInterface
from src.core.config import MEMGRAPH_PORT, logger

# ---------------------------------------------------
# Database Layer with Dependency Injection
# ---------------------------------------------------

class Memgraph(DatabaseInterface):
    """Memgraph database connection with connection pooling for sub-10ms P95 latency"""
    
    def __init__(self, host: str = None, port: int = None, max_retries: int = 5, retry_delay: float = 2.0, pool_size: int = None):
        from src.core.config import MEMGRAPH_HOST, MEMGRAPH_PORT, CONNECTION_POOL_SIZE
        host = host or MEMGRAPH_HOST
        port = port or MEMGRAPH_PORT
        pool_size = pool_size or CONNECTION_POOL_SIZE
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.pool_size = pool_size
        self.connection_pool = []
        self.pool_lock = asyncio.Lock()
        self.connection = None  # Primary connection for backward compatibility
        self._connect_with_retry()
    
    def _connect_with_retry(self):
        """Connect to Memgraph with connection pooling for performance"""
        # Create primary connection
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempting to connect to Memgraph at {self.host}:{self.port} (attempt {attempt + 1}/{self.max_retries})")
                self.connection = mgclient.connect(host=self.host, port=self.port)
                self.connection.autocommit = True
                logger.info("✅ Successfully connected to Memgraph")
                break
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to connect to Memgraph after {self.max_retries} attempts")
                    raise ConnectionError(f"Unable to connect to Memgraph at {self.host}:{self.port} after {self.max_retries} attempts: {e}")
        
        # Initialize connection pool for high-performance operations
        try:
            for i in range(self.pool_size):
                conn = mgclient.connect(host=self.host, port=self.port)
                conn.autocommit = True
                self.connection_pool.append(conn)
            logger.info(f"✅ Connection pool initialized with {self.pool_size} connections")
        except Exception as e:
            logger.warning(f"Failed to initialize connection pool: {e}. Using single connection.")

    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Ultra-optimized query execution for sub-10ms P95 latency"""
        max_retries = 1  # Single retry only for maximum speed
        retry_delay = 0.001  # 1ms retry delay
        
        for attempt in range(max_retries):
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, parameters or {})
                return cursor.fetchall()
            except Exception as e:
                if "conflicting transactions" in str(e) and attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Query execution failed: {e}")
                    raise

    async def get_pooled_connection(self):
        """Get a connection from the pool for high-performance operations"""
        async with self.pool_lock:
            if self.connection_pool:
                return self.connection_pool.pop()
            else:
                # Fallback to primary connection if pool is empty
                return self.connection

    async def return_pooled_connection(self, conn):
        """Return a connection to the pool"""
        if conn != self.connection:  # Don't return primary connection to pool
            async with self.pool_lock:
                if len(self.connection_pool) < self.pool_size:
                    self.connection_pool.append(conn)

    async def execute_query_pooled(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute query using connection pool for maximum performance"""
        conn = await self.get_pooled_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, parameters or {})
            return cursor.fetchall()
        finally:
            await self.return_pooled_connection(conn)

    async def execute_transaction(self, queries: List[str], parameters: Optional[List[Dict[str, Any]]] = None) -> Any:
        """Execute multiple queries in a transaction"""
        try:
            transaction = self.connection.begin()
            cursor = self.connection.cursor()
            
            results = []
            for i, query in enumerate(queries):
                if parameters and i < len(parameters):
                    cursor.execute(query, parameters[i])
                else:
                    cursor.execute(query)
                results.append(cursor.fetchall())
            
            transaction.commit()
            return results
        except Exception as e:
            transaction.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

    async def close(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Closed Memgraph connection")

    def execute(self, query: str, params: Optional[Dict] = None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or {})
        return cursor

    def transaction(self) -> 'MemgraphTransaction':
        self.connection.autocommit = False
        return MemgraphTransaction(self.connection)

class MemgraphTransaction(TransactionInterface):
    """Memgraph transaction context manager"""
    
    def __init__(self, connection):
        self.connection = connection
    
    async def __aenter__(self):
        """Enter transaction context"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context"""
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.autocommit = True

    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute query within transaction"""
        cursor = self.connection.cursor()
        if parameters:
            cursor.execute(query, parameters)
        else:
            cursor.execute(query)
        return cursor.fetchall()

    def execute(self, query: str, params: Optional[Dict] = None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or {})
        return cursor

    def __enter__(self) -> 'MemgraphTransaction':
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.autocommit = True

class DatabaseIndexManager:
    """Manages database indexes for optimal query performance"""
    
    def __init__(self, database: DatabaseInterface):
        self.database = database

    def create_indexes(self) -> None:
        """Create database indexes for optimal query performance"""
        logger.info("Creating database indexes for optimal performance...")
        
        indexes = [
            # Primary lookup indexes
            "CREATE INDEX ON :Frame(tickID)",
            "CREATE INDEX ON :Camera(cameraID)",
            
            # Track entity indexes - Essential lookups only
            # Note: TTL-related timestamp/last_updated indexes removed for better write performance
            "CREATE INDEX ON :BallTrack(track_id)",
            "CREATE INDEX ON :BallTrack(is_best)",             # Best ball detection filtering
            "CREATE INDEX ON :PlayerTrack(track_id)",
            
            # Camera parameters index
            "CREATE INDEX ON :CamParams(cameraID)",            # For camera-based queries
            
            # USD Scene Descriptor indexes (no TTL - persistent nodes)
            "CREATE INDEX ON :Scene_Descriptor(venue_id)",     # Singleton lookup
            "CREATE INDEX ON :FusedPlayer(id)",                # Player lookup by id
            "CREATE INDEX ON :FusedPlayer(status)",            # Filter by tracking status
            "CREATE INDEX ON :FusedPlayer(x)",                 # Spatial sorting/filtering (X coordinate)
            "CREATE INDEX ON :FusedPlayer(y)",                 # Spatial sorting/filtering (Y coordinate)
            "CREATE INDEX ON :FusedPlayer(z)",                 # Spatial sorting/filtering (Z coordinate)
            "CREATE INDEX ON :FusionBall3D(position_world)",       # Ball 3D position lookups
            "CREATE INDEX ON :FusionBall3D(status)",           # Ball fusion status filtering
            "CREATE INDEX ON :CameraConfig(cameraID)",         # Camera config lookup
            "CREATE INDEX ON :CameraConfig(role)",             # Camera role filtering
            "CREATE INDEX ON :CameraConfig(gimbal_position)",  # Camera gimbal position queries
            
            # Intent indexes (persistent nodes, no TTL)
            "CREATE INDEX ON :Intent(cameraID)",               # Intent lookup by camera
            "CREATE INDEX ON :Intent(status)",                 # Intent status filtering
        ]
        
        try:
            for index_query in indexes:
                try:
                    self.database.execute(index_query)
                    logger.debug(f"Created index: {index_query}")
                except Exception as e:
                    # Index may already exist - log but continue
                    if "already exists" in str(e).lower() or "constraint already exists" in str(e).lower():
                        logger.debug(f"Index already exists: {index_query}")
                    else:
                        logger.warning(f"Failed to create index '{index_query}': {e}")
            
            logger.info("Database indexes creation completed successfully")
            self._verify_critical_indexes()
            
        except Exception as e:
            logger.error(f"Error during index creation: {e}")
            # Don't fail startup if indexes can't be created

    def _verify_critical_indexes(self) -> None:
        """Verify that critical indexes exist for performance"""
        critical_indexes = [
            ("Frame", "tickID"),
            ("Camera", "cameraID")
        ]
        
        try:
            for label, property_name in critical_indexes:
                # Query to check if index exists (Memgraph specific)
                result = self.database.execute("SHOW INDEX INFO")
                indexes_exist = False
                
                if result:
                    for row in result:
                        # Check if our critical indexes are present
                        if label in str(row) and property_name in str(row):
                            indexes_exist = True
                            break
                
                if indexes_exist:
                    logger.info(f"✅ Critical index verified: {label}({property_name})")
                else:
                    logger.debug(f"ℹ️  Index status unknown: {label}({property_name}) - verification not supported")
                    
        except Exception as e:
            logger.debug(f"Could not verify indexes (this is normal on some Memgraph versions): {e}") 