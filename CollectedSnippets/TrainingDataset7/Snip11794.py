def process_lhs(self, compiler, connection, lhs=None):
        lhs_sql, params = super().process_lhs(compiler, connection, lhs)
        field_internal_type = self.lhs.output_field.get_internal_type()
        lhs_sql = (
            connection.ops.lookup_cast(self.lookup_name, field_internal_type) % lhs_sql
        )
        return lhs_sql, tuple(params)