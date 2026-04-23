def process_rhs(self, compiler, connection):
        dist_sql, dist_params = self.process_distance(compiler, connection)
        self.template_params["value"] = dist_sql
        rhs_sql, params = super().process_rhs(compiler, connection)
        return rhs_sql, (*params, *dist_params)