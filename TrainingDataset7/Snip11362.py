def as_sqlite(self, compiler, connection):
        template = "JSON_TYPE(%s, %s) IS NULL"
        if not self.rhs:
            template = "JSON_TYPE(%s, %s) IS NOT NULL"
        return HasKeyOrArrayIndex(self.lhs.lhs, self.lhs.key_name).as_sql(
            compiler,
            connection,
            template=template,
        )