def __getitem__(self, key):
        """
        Get a variable's value, starting at the current context and going
        upward
        """
        for d in reversed(self.dicts):
            if key in d:
                return d[key]
        raise KeyError(key)