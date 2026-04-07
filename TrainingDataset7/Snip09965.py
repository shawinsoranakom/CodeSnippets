def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
        return super().execute(query, params)