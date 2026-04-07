def as_sql(self, compiler, connection):
        return "'%s%s'" % (self.lower, self.upper), []