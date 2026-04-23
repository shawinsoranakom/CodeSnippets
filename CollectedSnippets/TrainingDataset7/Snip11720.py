def coalesce(self):
        # null on either side results in null for expression, wrap with
        # coalesce
        c = self.copy()
        c.set_source_expressions(
            [
                Coalesce(expression, Value(""))
                for expression in c.get_source_expressions()
            ]
        )
        return c