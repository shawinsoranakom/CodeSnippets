def __eq__(self, other):
        if not isinstance(other, Prefetch):
            return NotImplemented
        return self.prefetch_to == other.prefetch_to