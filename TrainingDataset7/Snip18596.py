def _execute_capture_statements(
            self, cursor, statements, parameters, verbosity, allow_quiet_fail=False
        ):
            self.tblspace_sqls = statements