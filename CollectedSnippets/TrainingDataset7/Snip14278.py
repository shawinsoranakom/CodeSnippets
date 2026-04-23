def __getitem__(self, key):
        """
        Retrieve the real value after stripping the prefix string (if
        present). If the prefix is present, pass the value through self.func
        before returning, otherwise return the raw value.
        """
        use_func = key.startswith(self.prefix)
        key = key.removeprefix(self.prefix)
        value = super().__getitem__(key)
        if use_func:
            return self.func(value)
        return value