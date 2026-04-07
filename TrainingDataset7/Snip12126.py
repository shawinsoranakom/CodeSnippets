def as_sql(self, compiler, connection):
        return str(self.ordinal), ()