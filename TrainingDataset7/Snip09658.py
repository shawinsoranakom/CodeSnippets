def _execute_allow_fail_statements(
        self, cursor, statements, parameters, verbosity, acceptable_ora_err
    ):
        """
        Execute statements which are allowed to fail silently if the Oracle
        error code given by `acceptable_ora_err` is raised. Return True if the
        statements execute without an exception, or False otherwise.
        """
        try:
            # Statement can fail when acceptable_ora_err is not None
            allow_quiet_fail = (
                acceptable_ora_err is not None and len(acceptable_ora_err) > 0
            )
            self._execute_statements(
                cursor,
                statements,
                parameters,
                verbosity,
                allow_quiet_fail=allow_quiet_fail,
            )
            return True
        except DatabaseError as err:
            description = str(err)
            if acceptable_ora_err is None or acceptable_ora_err not in description:
                raise
            return False