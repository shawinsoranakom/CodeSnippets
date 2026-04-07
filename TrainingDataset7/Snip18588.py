def _execute_raise_user_already_exists(
        self, cursor, statements, parameters, verbosity, allow_quiet_fail=False
    ):
        # Raise "user already exists" only in test user creation
        if statements and statements[0].startswith("CREATE USER"):
            raise DatabaseError(
                "ORA-01920: user name 'string' conflicts with another user or role name"
            )