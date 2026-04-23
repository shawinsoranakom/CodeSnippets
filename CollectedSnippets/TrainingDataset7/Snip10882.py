def as_sql(self, compiler, connection):
        if not connection.features.supports_default_keyword_in_insert:
            return compiler.compile(self.expression)
        return "DEFAULT", ()