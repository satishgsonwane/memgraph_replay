import asyncio
from typing import Any
from src.core.interfaces import CacheInterface

# ---------------------------------------------------
# Cache Management Component
# ---------------------------------------------------

class CacheManager(CacheInterface):
    """Thread-safe cache for detecting meaningful changes"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
        self._cache = {}

    def _is_meaningfully_different(self, a, b, tol=0.01):
        """Recursively compare two JSON-like structures."""
        if type(a) != type(b):
            return True

        if isinstance(a, dict):
            if a.keys() != b.keys():
                return True
            for k in a:
                if self._is_meaningfully_different(a[k], b[k], tol):
                    return True
            return False

        if isinstance(a, list):
            if len(a) != len(b):
                return True
            for v1, v2 in zip(a, b):
                if self._is_meaningfully_different(v1, v2, tol):
                    return True
            return False

        if isinstance(a, float) and isinstance(b, float):
            return abs(a - b) > tol

        return a != b

    def get(self, key: str) -> Any:
        """Get value from cache"""
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        self._cache[key] = value

    def has_changed(self, topic: str, new_data: Any, tol: float = 0.01) -> bool:
        """Check for significant changes with thread safety."""
        last = self._cache.get(topic)
        if last is not None and not self._is_meaningfully_different(last, new_data, tol):
            return False
        self._cache[topic] = new_data
        return True

    def has_meaningful_change(self, topic: str, new_data: Any, tol: float = 0.01) -> bool:
        """Alias for has_changed to maintain test compatibility"""
        return self.has_changed(topic, new_data, tol)

    async def has_meaningful_change(self, topic: str, new_data: Any, tol: float = 0.01) -> bool:
        """Check for significant changes with thread safety."""
        async with self._lock:
            last = self._cache.get(topic)
            if last is not None and not self._is_meaningfully_different(last, new_data, tol):
                return False
            self._cache[topic] = new_data
            return True

    async def clear_cache(self) -> None:
        async with self._lock:
            self._cache.clear()

    def has_meaningful_change_sync(self, topic: str, new_data: Any, tol: float = 0.01) -> bool:
        """Synchronous version for performance-critical paths"""
        last = self._cache.get(topic)
        if last is not None and not self._is_meaningfully_different(last, new_data, tol):
            return False
        self._cache[topic] = new_data
        return True 