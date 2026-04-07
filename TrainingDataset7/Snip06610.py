def as_sql(self, connection, lookup, template_params, sql_params):
        template_params["mask"] = sql_params[-1]
        return super().as_sql(connection, lookup, template_params, sql_params[:-1])