def as_sql(self, compiler, connection):
        lhs, lhs_params = compiler.compile(self.lhs)
        return "(%s) %%%% 3" % lhs, lhs_params