def subtract_temporals(self, internal_type, lhs, rhs):
        lhs_sql, lhs_params = lhs
        rhs_sql, rhs_params = rhs
        if internal_type == "TimeField":
            if self.connection.mysql_is_mariadb:
                # MariaDB includes the microsecond component in TIME_TO_SEC as
                # a decimal. MySQL returns an integer without microseconds.
                return (
                    "CAST((TIME_TO_SEC(%(lhs)s) - TIME_TO_SEC(%(rhs)s)) "
                    "* 1000000 AS SIGNED)"
                ) % {
                    "lhs": lhs_sql,
                    "rhs": rhs_sql,
                }, (
                    *lhs_params,
                    *rhs_params,
                )
            return (
                "((TIME_TO_SEC(%(lhs)s) * 1000000 + MICROSECOND(%(lhs)s)) -"
                " (TIME_TO_SEC(%(rhs)s) * 1000000 + MICROSECOND(%(rhs)s)))"
            ) % {"lhs": lhs_sql, "rhs": rhs_sql}, tuple(lhs_params) * 2 + tuple(
                rhs_params
            ) * 2
        params = (*rhs_params, *lhs_params)
        return "TIMESTAMPDIFF(MICROSECOND, %s, %s)" % (rhs_sql, lhs_sql), params