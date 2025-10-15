import asyncio
from collections import Counter
from typing import Dict, Any
from src.core.interfaces import MetricsInterface

# ---------------------------------------------------
# Metrics Collection Component
# ---------------------------------------------------

class MetricsCollector(MetricsInterface):
    """Thread-safe metrics collection with async locks"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
        self._metrics = {
            "total_messages_received": Counter(),
            "items_flushed_per_batch": [],
            "batch_latencies": [],
            "validation_errors": Counter(),
            "dropped_messages": Counter()
        }

    def record_message_processed(self, topic: str, processing_time: float) -> None:
        """Record message processing metrics"""
        self._metrics["total_messages_received"][topic] += 1

    def record_batch_processed(self, topic: str, batch_size: int, processing_time: float) -> None:
        """Record batch processing metrics"""
        self._metrics["items_flushed_per_batch"].append(batch_size)
        self._metrics["batch_latencies"].append(processing_time)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        total = sum(self._metrics["total_messages_received"].values())
        avg_ms = (1000 * sum(self._metrics["batch_latencies"]) / 
                 len(self._metrics["batch_latencies"])) if self._metrics["batch_latencies"] else 0
        p95_ms = (1000 * sorted(self._metrics["batch_latencies"])[int(0.95 * len(self._metrics["batch_latencies"]))] 
                 if self._metrics["batch_latencies"] else 0)
        validation_errors = sum(self._metrics["validation_errors"].values())
        
        return {
            "total_received": total,
            "avg_batch_ms": avg_ms,
            "p95_batch_ms": p95_ms,
            "validation_errors": validation_errors
        }

    async def record_message_received(self, subject: str) -> None:
        async with self._lock:
            self._metrics["total_messages_received"][subject] += 1

    async def record_validation_error(self, topic: str) -> None:
        async with self._lock:
            self._metrics["validation_errors"][topic] += 1

    async def record_dropped_message(self, topic: str) -> None:
        async with self._lock:
            self._metrics["dropped_messages"][topic] += 1

    async def record_batch_metrics(self, items_flushed: int, latency: float) -> None:
        async with self._lock:
            self._metrics["items_flushed_per_batch"].append(items_flushed)
            self._metrics["batch_latencies"].append(latency)

    async def get_metrics_summary(self) -> Dict[str, Any]:
        async with self._lock:
            return self.get_metrics()

    def record_validation_error_sync(self, topic: str) -> None:
        """Synchronous version for performance-critical paths"""
        self._metrics["validation_errors"][topic] += 1

    def record_dropped_message_sync(self, topic: str) -> None:
        """Synchronous version for performance-critical paths"""
        self._metrics["dropped_messages"][topic] += 1 