def as_sql(self, compiler, connection):
        sql, params = compiler.compile(self.config)
        return "%s::regconfig" % sql, params