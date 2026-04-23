def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return "from_unixtime({})".format(lhs), params