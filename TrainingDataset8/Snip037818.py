def ttl(self) -> float:
        return cast(float, self._mem_cache.ttl)