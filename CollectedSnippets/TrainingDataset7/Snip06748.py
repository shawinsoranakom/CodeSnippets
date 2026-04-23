def as_sql(self, connection, lookup, template_params, sql_params):
        sql_template = self.sql_template or lookup.sql_template or self.default_template
        template_params.update({"op": self.op, "func": self.func})
        return sql_template % template_params, sql_params