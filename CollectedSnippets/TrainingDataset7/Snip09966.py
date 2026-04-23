def executemany(self, query, param_list):
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        # Peek carefully as a generator can be passed instead of a list/tuple.
        peekable, param_list = tee(iter(param_list))
        if (params := next(peekable, None)) and isinstance(params, Mapping):
            param_names = list(params)
        else:
            param_names = None
        query = self.convert_query(query, param_names=param_names)
        return super().executemany(query, param_list)