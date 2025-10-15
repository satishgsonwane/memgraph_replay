"""
Protocol interfaces for the OZ Game State Service
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio

class DatabaseInterface(ABC):
    """Interface for database operations"""
    
    @abstractmethod
    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a Cypher query"""
        pass
    
    @abstractmethod
    async def execute_transaction(self, queries: List[str], parameters: Optional[List[Dict[str, Any]]] = None) -> Any:
        """Execute multiple queries in a transaction"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close database connection"""
        pass

class TransactionInterface(ABC):
    """Interface for transaction operations"""
    
    @abstractmethod
    async def __aenter__(self):
        """Enter transaction context"""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context"""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute query within transaction"""
        pass

class MetricsInterface(ABC):
    """Interface for metrics collection"""
    
    @abstractmethod
    def record_message_processed(self, topic: str, processing_time: float) -> None:
        """Record message processing metrics"""
        pass
    
    @abstractmethod
    def record_batch_processed(self, topic: str, batch_size: int, processing_time: float) -> None:
        """Record batch processing metrics"""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        pass

class CacheInterface(ABC):
    """Interface for caching operations"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        pass
    
    @abstractmethod
    def has_changed(self, key: str, value: Any) -> bool:
        """Check if value has changed"""
        pass

class CypherBuilderInterface(ABC):
    """Interface for Cypher query building"""
    
    @abstractmethod
    def build_queries(self, topic: str, payload: Dict[str, Any], tick_id: int) -> List[str]:
        """Build Cypher queries from message payload"""
        pass

class QueryExecutorInterface(ABC):
    """Interface for query execution"""
    
    @abstractmethod
    async def execute_queries(self, queries: List[str], parameters: Optional[List[Dict[str, Any]]] = None) -> Any:
        """Execute multiple queries"""
        pass

class CleanupManagerInterface(ABC):
    """Interface for cleanup operations"""
    
    @abstractmethod
    async def cleanup_old_ticks(self, current_tick: int, rolling_window: int) -> None:
        """Clean up old data based on rolling window"""
        pass

class BatchProcessorInterface(ABC):
    """Interface for batch processing"""
    
    @abstractmethod
    async def add_queries(self, topic: str, queries: List[str]) -> None:
        """Add queries to batch"""
        pass
    
    @abstractmethod
    async def process_all_batches(self) -> None:
        """Process all pending batches"""
        pass

 