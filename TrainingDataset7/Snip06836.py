def process_distance(self, compiler, connection):
        dist_param = self.rhs_params[0]
        return (
            compiler.compile(dist_param.resolve_expression(compiler.query))
            if hasattr(dist_param, "resolve_expression")
            else (
                "%s",
                connection.ops.get_distance(
                    self.lhs.output_field, self.rhs_params, self.lookup_name
                ),
            )
        )