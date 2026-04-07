def quote_name(self, name):
        """
        A wrapper around connection.ops.quote_name that memoizes quoted
        name values.
        """
        if (quoted := self.quote_cache.get(name)) is not None:
            return quoted
        quoted = self.connection.ops.quote_name(name)
        self.quote_cache[name] = quoted
        return quoted