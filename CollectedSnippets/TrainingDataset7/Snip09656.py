def _destroy_test_user(self, cursor, parameters, verbosity):
        if verbosity >= 2:
            self.log("_destroy_test_user(): user=%s" % parameters["user"])
            self.log("Be patient. This can take some time...")
        statements = [
            "DROP USER %(user)s CASCADE",
        ]
        self._execute_statements(cursor, statements, parameters, verbosity)