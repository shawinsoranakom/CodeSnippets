def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return "(%s -> %%s)" % lhs, (*params, self.key_name)