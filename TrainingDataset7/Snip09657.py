def _execute_statements(
        self, cursor, statements, parameters, verbosity, allow_quiet_fail=False
    ):
        for template in statements:
            stmt = template % parameters
            if verbosity >= 2:
                print(stmt)
            try:
                cursor.execute(stmt)
            except Exception as err:
                if (not allow_quiet_fail) or verbosity >= 2:
                    self.log("Failed (%s)" % (err))
                raise