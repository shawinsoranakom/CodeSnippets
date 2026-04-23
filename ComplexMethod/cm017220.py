def _create_test_user(self, cursor, parameters, verbosity, keepdb=False):
        if verbosity >= 2:
            self.log("_create_test_user(): username = %s" % parameters["user"])
        statements = [
            """CREATE USER %(user)s
               IDENTIFIED BY "%(password)s"
               DEFAULT TABLESPACE %(tblspace)s
               TEMPORARY TABLESPACE %(tblspace_temp)s
               QUOTA UNLIMITED ON %(tblspace)s
            """,
            """GRANT CREATE SESSION,
                     CREATE TABLE,
                     CREATE SEQUENCE,
                     CREATE PROCEDURE,
                     CREATE TRIGGER
               TO %(user)s""",
        ]
        # Ignore "user already exists" error when keepdb is on
        acceptable_ora_err = "ORA-01920" if keepdb else None
        success = self._execute_allow_fail_statements(
            cursor, statements, parameters, verbosity, acceptable_ora_err
        )
        # If the password was randomly generated, change the user accordingly.
        if not success and self._test_settings_get("PASSWORD") is None:
            set_password = 'ALTER USER %(user)s IDENTIFIED BY "%(password)s"'
            self._execute_statements(cursor, [set_password], parameters, verbosity)
        # Most test suites can be run without "create view" and
        # "create materialized view" privileges. But some need it.
        for object_type in ("VIEW", "MATERIALIZED VIEW"):
            extra = "GRANT CREATE %(object_type)s TO %(user)s"
            parameters["object_type"] = object_type
            success = self._execute_allow_fail_statements(
                cursor, [extra], parameters, verbosity, "ORA-01031"
            )
            if not success and verbosity >= 2:
                self.log(
                    "Failed to grant CREATE %s permission to test user. This may be ok."
                    % object_type
                )