def as_sql(self, connection, lookup, template_params, sql_params):
        sql, params = super().as_sql(connection, lookup, template_params, sql_params)
        return "%s > 0" % sql, params