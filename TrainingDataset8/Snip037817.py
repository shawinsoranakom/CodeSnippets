def max_entries(self) -> float:
        return cast(float, self._mem_cache.maxsize)