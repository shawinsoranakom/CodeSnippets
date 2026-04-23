def as_sql(self, compiler, connection):
        return compiler.compile(self.resolved_condition)