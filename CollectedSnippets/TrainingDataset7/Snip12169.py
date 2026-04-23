def _as_sql(self, query):
        delete = "DELETE FROM %s" % self.quote_name(query.base_table)
        try:
            where, params = self.compile(query.where)
        except FullResultSet:
            return delete, ()
        return f"{delete} WHERE {where}", tuple(params)