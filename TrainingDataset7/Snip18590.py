def _execute_raise_insufficient_privileges(
        self, cursor, statements, parameters, verbosity, allow_quiet_fail=False
    ):
        raise DatabaseError("ORA-01031: insufficient privileges")