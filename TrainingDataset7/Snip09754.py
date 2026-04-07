def subtract_temporals(self, internal_type, lhs, rhs):
        if internal_type == "DateField":
            lhs_sql, lhs_params = lhs
            rhs_sql, rhs_params = rhs
            params = (*lhs_params, *rhs_params)
            return (
                "NUMTODSINTERVAL(TO_NUMBER(%s - %s), 'DAY')" % (lhs_sql, rhs_sql),
                params,
            )
        return super().subtract_temporals(internal_type, lhs, rhs)