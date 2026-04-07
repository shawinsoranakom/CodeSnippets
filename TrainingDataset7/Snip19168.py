def __getstate__(self):
        self.locked = self.cache._lock.locked()
        return {}