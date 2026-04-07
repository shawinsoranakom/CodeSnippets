def prepare_join_on_clause(self, lhs_table, lhs_field, rhs_table, rhs_field):
        lhs_expr = Col(lhs_table, lhs_field)
        rhs_expr = Col(rhs_table, rhs_field)

        return lhs_expr, rhs_expr