def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        if not lhs.endswith("]"):
            lhs = "(%s)" % lhs
        return "%s[%%s]" % lhs, (*params, self.index)