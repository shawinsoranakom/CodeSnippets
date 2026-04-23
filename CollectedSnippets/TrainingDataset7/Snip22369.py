def as_sql(self, compiler, connection):
        qn = compiler.quote_name
        return "%s.%s = %%s" % (qn(self.alias), qn(self.col)), [self.value]