def __contains__(self, val: Any):
        return id(val) in self._stack