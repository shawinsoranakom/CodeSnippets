def as_sql(self, compiler, connection):
        qn = compiler.quote_name
        alias_str = (
            ""
            if self.table_alias == self.table_name
            else (" %s" % qn(self.table_alias))
        )
        base_sql = qn(self.table_name)
        return base_sql + alias_str, []