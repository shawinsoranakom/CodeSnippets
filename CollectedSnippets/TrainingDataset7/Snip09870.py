def prepare_join_on_clause(self, lhs_table, lhs_field, rhs_table, rhs_field):
        lhs_expr, rhs_expr = super().prepare_join_on_clause(
            lhs_table, lhs_field, rhs_table, rhs_field
        )

        if lhs_field.db_type(self.connection) != rhs_field.db_type(self.connection):
            rhs_expr = Cast(rhs_expr, lhs_field)

        return lhs_expr, rhs_expr