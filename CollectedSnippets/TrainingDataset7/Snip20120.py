def as_sql(self, compiler, connection):
        lhs, lhs_params = compiler.compile(self.lhs)
        return "SUBSTR(CAST(%s AS CHAR(2)), 2, 1)" % lhs, lhs_params