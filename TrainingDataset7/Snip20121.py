def as_sql(self, compiler, connection):
        lhs, lhs_params = compiler.compile(self.lhs)
        return "UPPER(%s)" % lhs, lhs_params