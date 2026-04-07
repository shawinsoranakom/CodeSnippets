def as_oracle(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        if connection.features.supports_primitives_in_json_field:
            lhs = f"JSON({lhs})"
            rhs = f"JSON({rhs})"
        return f"JSON_EQUAL({lhs}, {rhs} ERROR ON ERROR)", (*lhs_params, *rhs_params)