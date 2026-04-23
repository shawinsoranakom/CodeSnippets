def __contains__(self, key):
        return any(key in d for d in self.dicts)