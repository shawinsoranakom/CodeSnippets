def compose_sql(self, sql, params):
        return mogrify(sql, params, self.connection)