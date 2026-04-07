def _execute_raise_tablespace_already_exists(
        self, cursor, statements, parameters, verbosity, allow_quiet_fail=False
    ):
        raise DatabaseError("ORA-01543: tablespace 'string' already exists")