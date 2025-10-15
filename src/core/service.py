import asyncio
import orjson
import time
from typing import Optional, Any
from nats.aio.client import Client as NATS

from .interfaces import (
    DatabaseInterface, 
    MetricsInterface, 
    CacheInterface, 
    CypherBuilderInterface,
    QueryExecutorInterface,
    CleanupManagerInterface,
    BatchProcessorInterface
)
from database.repository import Memgraph, DatabaseIndexManager
from src.utils.metrics import MetricsCollector
from src.utils.cache import CacheManager
from src.processors.cypher_builder import CypherBuilder
from src.processors.query_executor import QueryExecutor
from src.processors.cleanup_manager import CleanupManager
from src.processors.batch_processor import BatchProcessor
from .config import BridgeConfig, LOW_VALUE_TOPICS, logger, CLEANUP_INTERVAL, CLEANUP_INTERVAL_SECONDS

# ---------------------------------------------------
# Main Bridge Class with Composition
# ---------------------------------------------------

class NATSMemgraphBridge:
    """Main bridge class using composition and dependency injection"""
    
    def __init__(self, 
                 config: BridgeConfig,
                 database: Optional[DatabaseInterface] = None,
                 metrics: Optional[MetricsInterface] = None,
                 cache: Optional[CacheInterface] = None,
                 cypher_builder: Optional[CypherBuilderInterface] = None,
                 query_executor: Optional[QueryExecutorInterface] = None,
                 cleanup_manager: Optional[CleanupManagerInterface] = None,
                 batch_processor: Optional[BatchProcessorInterface] = None):
        
        # Configuration
        self.config = config
        
        # Dependency injection with defaults - delay database connection
        self._database_config = {'host': config.memgraph_host, 'port': config.memgraph_port}
        self.database = database  # Will be initialized when needed
        self.metrics = metrics or MetricsCollector()
        self.cache = cache or CacheManager()
        
        # Store injected components
        self.cypher_builder = cypher_builder
        self.query_executor = query_executor
        self.cleanup_manager = cleanup_manager
        self.batch_processor = batch_processor
        
        # Thread-safe state
        self._state_lock = asyncio.Lock()
        self._current_tick = 0
        self._tick_initialized = False
        self._shutdown_requested = False
        self._processed_ticks = set()  # Track processed ticks to avoid duplicates
        self._scene_initialized = False  # Track if Scene_Descriptor has been initialized
        
        # NATS clients - single connection setup
        self.nc = None  # NATS connection for all topics
        self.nc_local = None  # Local NATS connection (same as nc now)
        
        # Initialize database indexes for performance - will be done after connection
        self.index_manager = None  # Will be initialized when database is ready

    def _ensure_database_connected(self):
        """Ensure database is connected before use"""
        if self.database is None:
            logger.info("Initializing database connection...")
            self.database = Memgraph(**self._database_config)
            self.index_manager = DatabaseIndexManager(self.database)
            self.index_manager.create_indexes()
            
            # Initialize composed components that depend on database
            if not hasattr(self, 'query_executor') or self.query_executor is None:
                self.query_executor = QueryExecutor(self.database)
            if not hasattr(self, 'cleanup_manager') or self.cleanup_manager is None:
                self.cleanup_manager = CleanupManager(self.database, self.config)
            if not hasattr(self, 'batch_processor') or self.batch_processor is None:
                self.batch_processor = BatchProcessor(self.query_executor, self.metrics, self.config.max_batch_size)
            if not hasattr(self, 'cypher_builder') or self.cypher_builder is None:
                self.cypher_builder = CypherBuilder(self.cache, self.metrics)
            
            # Initialize USD Scene_Descriptor structure once on startup
            self._initialize_usd_scene()
    
    def _initialize_usd_scene(self):
        """Initialize USD Scene_Descriptor structure - deferred to async context"""
        try:
            # Check if Scene_Descriptor already exists to avoid reinitializing
            cursor = self.database.connection.cursor()
            cursor.execute("MATCH (sd:Scene_Descriptor) RETURN count(sd)")
            result = cursor.fetchall()
            if result and result[0][0] > 0:
                logger.info("Scene_Descriptor already exists, skipping initialization")
                self._scene_initialized = True
                return
            
            # Mark as needing initialization (will be done in async context)
            self._scene_initialized = False
            logger.info("Scene_Descriptor will be initialized in async context")
            
        except Exception as e:
            logger.error(f"❌ Failed to check Scene_Descriptor: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._scene_initialized = False

    @property
    def current_tick(self) -> int:
        """Simple atomic read of current tick (int assignment is atomic in Python)"""
        return self._current_tick

    def _set_current_tick(self, tick: int) -> None:
        """Simple atomic write of current tick"""
        self._current_tick = tick
        self._tick_initialized = True

    def is_low_value_topic(self, subject: str, payload: dict) -> bool:
        if any(subject.startswith(prefix) for prefix in LOW_VALUE_TOPICS):
            return len(payload) <= 3
        return False

    async def message_handler(self, msg):
        """Handle incoming NATS message with thread safety"""
        subject = msg.subject
        data = msg.data

        try:
            payload = orjson.loads(data)

            if self.is_low_value_topic(subject, payload):
                return

            await self.metrics.record_message_received(subject)
            
            # Handle tickperframe messages to update current tick
            if subject.startswith("tickperframe"):
                count = payload.get("count", 0)
                self._set_current_tick(count)
                await self.batch_processor.add_to_buffer(subject, payload)
            elif subject.startswith("ptzinfo."):
                await self.batch_processor.add_to_buffer(subject, payload)
            elif subject.startswith("all_tracks."):
                if self.cache.has_meaningful_change_sync(subject, payload, tol=0.001):
                    await self.batch_processor.add_to_buffer(subject, payload)
            elif subject.startswith("fusion.ball_3d"):
                await self.batch_processor.add_to_buffer(subject, payload)
            elif subject.startswith("fused_players"):
                # USD schema: fused players from fusion algorithm
                await self.batch_processor.add_to_buffer(subject, payload)
            elif subject.startswith("intents.processed"):
                # Intent processing: camera intent state (persistent, no TTL)
                await self.batch_processor.add_to_buffer(subject, payload)
            else:
                # Skip all other topics
                logger.debug(f"Skipping unsupported topic: {subject}")
        except Exception as e:
            logger.error(f"JSON parse error for {subject}: {e}")
            self.metrics.record_dropped_message_sync(subject)

    async def process_batch_loop(self):
        """Main batch processing loop with enhanced monitoring"""
        logger.info("Starting batch processing loop...")
        
        # Ensure database is connected before starting batch processing
        self._ensure_database_connected()
        
        # Initialize Scene_Descriptor in async context if needed
        if not self._scene_initialized:
            try:
                from src.utils.scene_initializer import SceneInitializer
                initializer = SceneInitializer(self.database)
                await initializer.initialize_all()
                self._scene_initialized = True
                logger.info("✅ USD Scene initialization completed successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize USD scene in async context: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        last_cleanup_time = time.time()
        last_metric_time = time.time()
        
        while not self._shutdown_requested:
            await asyncio.sleep(self.config.batch_interval)
            
            current_tick = self.current_tick
            if current_tick == 0:
                continue
                
            # Add periodic heartbeat to detect hangs
            if current_tick % 1000 == 0:  # Every 1000 ticks
                logger.debug(f"Service heartbeat - tick: {current_tick}, buffer_size: {await self.batch_processor.get_buffer_size()}")
                
            # Get buffer sizes before processing for monitoring
            buffer_sizes_before = await self.batch_processor.get_topic_buffer_sizes()
            start_time = time.perf_counter()
            
            try:
                # Get real-time batch info
                batch_info = await self.batch_processor.get_real_time_batch_info(buffer_sizes_before)
                
                items_processed = await self.batch_processor.process_batch(self.cypher_builder, current_tick)
                
                if items_processed > 0:
                    latency = time.perf_counter() - start_time
                    await self.metrics.record_batch_metrics(items_processed, latency)
                    
                    # Real-time batch monitoring every 10 batches
                    if batch_info["batch_number"] % 10 == 0:
                        top_topics = sorted(buffer_sizes_before.items(), 
                                          key=lambda x: x[1], reverse=True)[:3]
                        # logger.info(f"[ConcurrentBatch] {batch_info['active_topics']} topics, "
                        #           f"{items_processed} items, {latency*1000:.1f}ms, "
                        #           f"AvgConcurrent={batch_info['avg_concurrent_topics']:.1f}, "
                        #           f"TopTopics: {top_topics}")

                # Time-based cleanup using cleanup_interval_seconds
                current_time = time.time()
                cleanup_interval_seconds = self.config.cleanup_interval_seconds
                
                if current_time >= last_cleanup_time + cleanup_interval_seconds:
                    try:
                        cleanup_start = time.perf_counter()
                        await self.cleanup_manager.cleanup_old_data_by_time()
                        cleanup_duration = time.perf_counter() - cleanup_start
                        logger.debug(f"TTL cleanup completed in {cleanup_duration*1000:.2f}ms at tick {current_tick}")
                    except Exception as e:
                        logger.error(f"TTL cleanup failed: {e}")
                        import traceback
                        logger.error(f"Cleanup traceback: {traceback.format_exc()}")
                    last_cleanup_time = current_time

                # Use time-based metrics interval (every 2 seconds)
                current_time = time.time()
                metrics_interval_seconds = 2.0  # Print metrics every 2 seconds
                if current_time >= last_metric_time + metrics_interval_seconds:
                    metrics_summary = await self.metrics.get_metrics_summary()
                    topic_buffer_sizes = await self.batch_processor.get_topic_buffer_sizes()
                    fill_rates = await self.batch_processor.get_fill_rates()
                    active_topics = len([t for t, size in topic_buffer_sizes.items() if size > 0])
                    
                    logger.info(f"[Metrics] Received={metrics_summary['total_received']} "
                            f"AvgBatch={metrics_summary['avg_batch_ms']:.2f}ms "
                            f"P95={metrics_summary['p95_batch_ms']:.2f}ms "
                            f"DroppedMessages={metrics_summary['validation_errors']} "
                            f"ActiveTopics={active_topics}")
                    
                    # Log top topics by buffer size for monitoring
                    if topic_buffer_sizes:
                        top_topics = sorted(topic_buffer_sizes.items(), key=lambda x: x[1], reverse=True)[:5]
                        top_topics_str = ", ".join([f"{topic}:{size}" for topic, size in top_topics if size > 0])
                        if top_topics_str:
                            logger.info(f"[TopicBuffers] {top_topics_str}")
                    
                    # Fill rate monitoring
                    if fill_rates:
                        high_fill_topics = [(t, r) for t, r in fill_rates.items() 
                                          if r["fill_rate"] > 10]  # >10 msg/sec
                        if high_fill_topics:
                            rate_str = ", ".join([f"{topic}:+{rate['fill_rate']:.1f}/s,-{rate['process_rate']:.1f}/s" 
                                                for topic, rate in high_fill_topics[:5]])
                            # logger.info(f"[FillRates] {rate_str}")
                    
                    last_metric_time = current_time

            except Exception as e:
                logger.error(f"Error during batch processing: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

    async def connect_and_subscribe(self):
        """Connect to NATS server and set up subscriptions"""
        # Connect to NATS server for all topics
        self.nc = NATS()
        await self.nc.connect(servers=[self.config.nats_url])
        logger.info(f"✅ Connected to NATS server: {self.config.nats_url}")
        
        # Set local connection to same as main connection
        self.nc_local = self.nc
        
        logger.info("Subscribing to topics...")
        
        # Subscribe to all topics on single NATS server
        await self.nc.subscribe("tickperframe", cb=self.message_handler)
        await self.nc.subscribe("all_tracks.*", cb=self.message_handler)
        await self.nc.subscribe("ptzinfo.*", cb=self.message_handler)
        await self.nc.subscribe("fusion.ball_3d", cb=self.message_handler)
        await self.nc.subscribe("intents.processed", cb=self.message_handler)
        await self.nc.subscribe("fused_players", cb=self.message_handler)
        logger.info(f"✅ Subscribed to all topics on {self.config.nats_url}")

        logger.info("All subscriptions complete.")

    async def run(self):
        """Main method to run the bridge"""
        await self.connect_and_subscribe()
        
        # logger.info(f"Starting batch processor with time-based TTL: {self.config.cleanup_interval_seconds}s cleanup interval, {self.config.rolling_window_seconds}s rolling window")
        await self.process_batch_loop()

    async def close(self):
        """Gracefully shutdown the bridge and clean up all resources"""
        logger.info("Starting graceful shutdown...")
        
        try:
            # Step 1: Signal shutdown to stop batch processing loop
            self._shutdown_requested = True
            logger.info("Shutdown signal sent to batch processor.")
            
            # Give the batch processor a moment to finish current iteration
            await asyncio.sleep(self.config.batch_interval * 2)
            
            # Step 2: Stop accepting new messages by closing NATS connection
            if self.nc and not self.nc.is_closed:
                logger.info("Closing NATS connection...")
                await self.nc.close()
                logger.info("NATS connection closed.")
            
            # Note: nc_local is same as nc, so no need to close separately
            
            # Step 4: Process any remaining items in the batch buffer (if initialized)
            if hasattr(self, 'batch_processor') and self.batch_processor is not None:
                logger.info("Processing remaining items in batch buffer...")
                remaining_items = await self.batch_processor.get_buffer_size()
                if remaining_items > 0:
                    logger.info(f"Processing {remaining_items} remaining items...")
                    if hasattr(self, 'cypher_builder') and self.cypher_builder is not None:
                        items_processed = await self.batch_processor.process_batch(self.cypher_builder, self.current_tick)
                        logger.info(f"Processed {items_processed} remaining items.")
            
            # Step 5: Clear caches (if initialized)
            if hasattr(self, 'cache') and self.cache is not None:
                logger.info("Clearing caches...")
                await self.cache.clear_cache()
            
            # Step 6: Get final metrics summary (if initialized)
            if hasattr(self, 'metrics') and self.metrics is not None:
                logger.info("Generating final metrics report...")
                final_metrics = await self.metrics.get_metrics_summary()
                logger.info(f"Final metrics: {final_metrics}")
            
            logger.info("Graceful shutdown completed successfully.")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
            import traceback
            logger.error(f"Shutdown traceback: {traceback.format_exc()}")

    async def shutdown(self):
        """Shutdown method for signal handlers"""
        await self.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with automatic cleanup"""
        await self.close() 