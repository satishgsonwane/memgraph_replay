import asyncio
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Any, List
from src.core.interfaces import (
    CypherBuilderInterface, 
    QueryExecutorInterface, 
    MetricsInterface
)
from src.core.config import MAX_BATCH_SIZE

# ---------------------------------------------------
# Batch Processing Component
# ---------------------------------------------------

class BatchProcessor:
    """
    Thread-safe batch processing with per-topic locks for better concurrency.
    
    Performance Improvements over single-lock approach:
    - Parallel processing: Different topics can be processed simultaneously
    - Reduced contention: Only topics accessing same buffer compete for locks  
    - Better throughput: Especially beneficial with multiple cameras/topics
    - Lock granularity: Fine-grained locking minimizes critical sections
    """
    
    def __init__(self, query_executor: QueryExecutorInterface, metrics: MetricsInterface, 
                 max_batch_size: int = MAX_BATCH_SIZE):
        self.query_executor = query_executor
        self.metrics = metrics
        self._max_batch_size = max_batch_size
        self._config_lock = asyncio.Lock()
        
        # Per-topic locks for fine-grained concurrency
        self._topic_locks = defaultdict(asyncio.Lock)
        self._buffer = defaultdict(list)
        self._global_lock = asyncio.Lock()  # Only for topic management operations
        
        # Buffer fill rate monitoring
        self._topic_fill_rates = defaultdict(int)  # messages added per topic
        self._topic_process_rates = defaultdict(int)  # messages processed per topic
        self._rate_window_start = time.time()
        self._rate_window_size = 10.0  # 10 second windows
        self._last_buffer_sizes = defaultdict(int)
        
        # Real-time batch monitoring
        self._batch_count = 0
        self._concurrent_topics_history = []

    @property
    def max_batch_size(self) -> int:
        """Thread-safe getter for max_batch_size"""
        return self._max_batch_size

    async def update_max_batch_size(self, new_size: int) -> None:
        """Thread-safe setter for max_batch_size"""
        async with self._config_lock:
            old_size = self._max_batch_size
            self._max_batch_size = new_size
            from src.core.config import logger
            logger.info(f"BatchProcessor: max_batch_size changed from {old_size} to {new_size}")

    async def add_queries(self, topic: str, queries: List[str]) -> None:
        """Add queries to batch buffer with per-topic locking."""
        async with self._topic_locks[topic]:
            self._buffer[topic].extend(queries)
            self._topic_fill_rates[topic] += len(queries)  # Track fill rate

    async def add_to_buffer(self, topic: str, data: Any) -> None:
        """Thread-safe addition with per-topic locking and rate monitoring."""
        async with self._topic_locks[topic]:
            self._buffer[topic].append(data)
            self._topic_fill_rates[topic] += 1  # Track fill rate

    async def get_buffer_size(self) -> int:
        """Get current buffer size thread-safely."""
        # Use global lock only for reading topic list, then sum per-topic
        async with self._global_lock:
            topics = list(self._buffer.keys())
        
        total_size = 0
        for topic in topics:
            async with self._topic_locks[topic]:
                total_size += len(self._buffer[topic])
        return total_size

    async def get_topic_buffer_sizes(self) -> Dict[str, int]:
        """Get buffer sizes per topic for monitoring."""
        async with self._global_lock:
            topics = list(self._buffer.keys())
        
        topic_sizes = {}
        for topic in topics:
            async with self._topic_locks[topic]:
                topic_sizes[topic] = len(self._buffer[topic])
        return topic_sizes

    async def get_fill_rates(self) -> Dict[str, Dict[str, float]]:
        """Get buffer fill and process rates per topic."""
        current_time = time.time()
        window_duration = current_time - self._rate_window_start
        
        if window_duration < self._rate_window_size:
            return {}  # Not enough time elapsed
        
        rates = {}
        async with self._global_lock:
            for topic in self._topic_fill_rates:
                fill_rate = self._topic_fill_rates[topic] / window_duration
                process_rate = self._topic_process_rates[topic] / window_duration
                rates[topic] = {
                    "fill_rate": fill_rate,
                    "process_rate": process_rate,
                    "net_rate": fill_rate - process_rate
                }
        
        # Reset counters for next window
        self._topic_fill_rates.clear()
        self._topic_process_rates.clear()
        self._rate_window_start = current_time
        
        return rates

    async def get_real_time_batch_info(self, buffer_sizes_before: Dict[str, int]) -> Dict[str, Any]:
        """Get real-time batch processing information."""
        active_topics = len([s for s in buffer_sizes_before.values() if s > 0])
        total_buffer = sum(buffer_sizes_before.values())
        
        self._concurrent_topics_history.append(active_topics)
        if len(self._concurrent_topics_history) > 100:  # Keep last 100 samples
            self._concurrent_topics_history.pop(0)
        
        avg_concurrent_topics = sum(self._concurrent_topics_history) / len(self._concurrent_topics_history)
        
        return {
            "active_topics": active_topics,
            "total_buffer": total_buffer,
            "avg_concurrent_topics": avg_concurrent_topics,
            "batch_number": self._batch_count
        }

    async def process_all_batches(self) -> int:
        """Process all pending batches with per-topic locking."""
        items_flushed = 0
        batch_groups = defaultdict(list)
        batch_data = []
        
        # Step 1: Get topic list (fast global operation)
        async with self._global_lock:
            topics = list(self._buffer.keys())
        
        # Step 2: Process each topic independently with per-topic locks
        for topic in topics:
            if items_flushed >= self.max_batch_size:
                break
                
            topic_items = 0
            async with self._topic_locks[topic]:
                # Collect items from this topic up to remaining batch size
                while (items_flushed + topic_items < self.max_batch_size 
                       and self._buffer[topic]):
                    data = self._buffer[topic].pop(0)
                    batch_data.append((topic, data))
                    topic_items += 1
                
                # Clean up empty topic buffers
                if not self._buffer[topic]:
                    # Remove from buffer under global lock to avoid race conditions
                    async with self._global_lock:
                        if not self._buffer[topic]:  # Double-check pattern
                            del self._buffer[topic]
            
            items_flushed += topic_items

        # Step 3: Process data with cypher builder (synchronous, fast!)
        for topic, data in batch_data:
            result = data  # data is already processed by cypher_builder
            if result:
                if isinstance(result, list):
                    for item in result:
                        if item and len(item) == 2:
                            batch_type, row = item
                            if batch_type and row:
                                if batch_type not in batch_groups:
                                    batch_groups[batch_type] = []
                                batch_groups[batch_type].append(row)
                else:
                    batch_type, row = result
                    if batch_type and row:
                        if batch_type not in batch_groups:
                            batch_groups[batch_type] = []
                        batch_groups[batch_type].append(row)

        # Step 4: Execute batch queries and track process rates
        if items_flushed > 0:
            # Use asyncio.create_task for non-blocking execution
            query_task = asyncio.create_task(self.query_executor.execute_queries(batch_groups))
            await query_task
            
            # Track process rates per topic
            for topic, data in batch_data:
                self._topic_process_rates[topic] += 1
            
            self._batch_count += 1
            
        return items_flushed

    async def process_batch(self, cypher_builder: CypherBuilderInterface, current_tick: int) -> int:
        """Ultra-optimized batch processing for sub-10ms P95 latency"""
        items_flushed = 0
        batch_groups = {}  # Pre-allocated dict instead of defaultdict
        
        # Add diagnostic logging for large batches
        if current_tick % 1000 == 0:  # Every 1000 ticks
            total_buffer = await self.get_buffer_size()
            logger.debug(f"Batch processor heartbeat - tick: {current_tick}, total_buffer: {total_buffer}")
        
        # Pre-allocate system timestamp once
        system_timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        cypher_builder.set_system_timestamp(system_timestamp)
        
        # Single atomic operation to extract all data
        batch_data = []
        async with self._global_lock:
            topics_to_process = list(self._buffer.keys())
            if not topics_to_process:
                return 0
            
            # Extract data in single pass to minimize lock time
            for topic in topics_to_process:
                if items_flushed >= self.max_batch_size:
                    break
                    
                buffer = self._buffer[topic]
                items_to_take = min(len(buffer), self.max_batch_size - items_flushed)
                
                if items_to_take > 0:
                    # Bulk extract using slice operation (faster than individual pops)
                    extracted_data = buffer[:items_to_take]
                    del buffer[:items_to_take]
                    
                    # Add to batch data
                    batch_data.extend([(topic, data) for data in extracted_data])
                    items_flushed += items_to_take
                    
                    # Clean up empty buffers
                    if not buffer:
                        del self._buffer[topic]

        # Ultra-fast data processing outside of any locks
        for topic, data in batch_data:
            result = cypher_builder.build_queries(topic, data, current_tick)
            if result:
                if isinstance(result, list):
                    for item in result:
                        if item and len(item) == 2:
                            batch_type, row = item
                            if batch_type and row:
                                if batch_type not in batch_groups:
                                    batch_groups[batch_type] = []
                                batch_groups[batch_type].append(row)
                else:
                    batch_type, row = result
                    if batch_type and row:
                        if batch_type not in batch_groups:
                            batch_groups[batch_type] = []
                        batch_groups[batch_type].append(row)

        # Execute queries if we have data
        if items_flushed > 0:
            await self.query_executor.execute_queries(batch_groups)
            
            # Update metrics
            for topic, _ in batch_data:
                self._topic_process_rates[topic] += 1
            
            self._batch_count += 1
            
        return items_flushed

    async def process_batch_memory_optimized(self, cypher_builder: CypherBuilderInterface, current_tick: int) -> int:
        """Memory-optimized batch processing for high-volume track data"""
        items_flushed = 0
        batch_groups = {}
        
        # Process in smaller chunks to reduce memory pressure
        max_chunk_size = 50  # Much smaller chunks for memory efficiency
        system_timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        cypher_builder.set_system_timestamp(system_timestamp)
        
        # Process topics in priority order (most memory-intensive first)
        topic_priority = ['all_tracks.', 'ptzinfo.', 'tickperframe']
        
        for priority_topic in topic_priority:
            if items_flushed >= max_chunk_size:
                break
                
            # Find topics matching this priority
            matching_topics = [t for t in self._buffer.keys() if t.startswith(priority_topic)]
            
            for topic in matching_topics:
                if items_flushed >= max_chunk_size:
                    break
                    
                async with self._topic_locks[topic]:
                    if not self._buffer[topic]:
                        continue
                        
                    # Process only a small chunk
                    chunk_size = min(len(self._buffer[topic]), max_chunk_size - items_flushed)
                    chunk_data = self._buffer[topic][:chunk_size]
                    del self._buffer[topic][:chunk_size]
                    
                    # Process chunk immediately
                    for data in chunk_data:
                        result = cypher_builder.build_queries(topic, data, current_tick)
                        if result:
                            if isinstance(result, list):
                                for item in result:
                                    if item and len(item) == 2:
                                        batch_type, row = item
                                        if batch_type and row:
                                            if batch_type not in batch_groups:
                                                batch_groups[batch_type] = []
                                            batch_groups[batch_type].append(row)
                            else:
                                batch_type, row = result
                                if batch_type and row:
                                    if batch_type not in batch_groups:
                                        batch_groups[batch_type] = []
                                    batch_groups[batch_type].append(row)
                    
                    items_flushed += chunk_size
                    
                    # Clean up empty buffers
                    if not self._buffer[topic]:
                        async with self._global_lock:
                            if not self._buffer[topic]:
                                del self._buffer[topic]
        
        # Execute queries if we have data
        if items_flushed > 0 and batch_groups:
            await self.query_executor.execute_queries(batch_groups)
            self._batch_count += 1
            
        return items_flushed 