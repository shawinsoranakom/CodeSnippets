def as_sql(self, compiler, connection):
        return "%s()" % self.name, []