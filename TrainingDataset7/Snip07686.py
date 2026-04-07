def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        # self.start is set to 1 if slice start is not provided.
        if self.end is None:
            return f"({lhs})[%s:]", (*params, self.start)
        else:
            return f"({lhs})[%s:%s]", (*params, self.start, self.end)