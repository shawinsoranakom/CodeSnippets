def instance(cls) -> "ComponentRegistry":
        """Returns the singleton ComponentRegistry"""
        # We use a double-checked locking optimization to avoid the overhead
        # of acquiring the lock in the common case:
        # https://en.wikipedia.org/wiki/Double-checked_locking
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = ComponentRegistry()
        return cls._instance