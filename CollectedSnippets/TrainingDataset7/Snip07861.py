def as_sql(self, compiler, connection, function=None, template=None):
        sql, params = super().as_sql(compiler, connection, function, template)
        if self.invert:
            sql = "!!(%s)" % sql
        return sql, params