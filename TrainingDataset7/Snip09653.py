def _execute_test_db_creation(self, cursor, parameters, verbosity, keepdb=False):
        if verbosity >= 2:
            self.log("_create_test_db(): dbname = %s" % parameters["user"])
        if self._test_database_oracle_managed_files():
            statements = [
                """
                CREATE TABLESPACE %(tblspace)s
                DATAFILE SIZE %(size)s
                AUTOEXTEND ON NEXT %(extsize)s MAXSIZE %(maxsize)s
                """,
                """
                CREATE TEMPORARY TABLESPACE %(tblspace_temp)s
                TEMPFILE SIZE %(size_tmp)s
                AUTOEXTEND ON NEXT %(extsize_tmp)s MAXSIZE %(maxsize_tmp)s
                """,
            ]
        else:
            statements = [
                """
                CREATE TABLESPACE %(tblspace)s
                DATAFILE '%(datafile)s' SIZE %(size)s REUSE
                AUTOEXTEND ON NEXT %(extsize)s MAXSIZE %(maxsize)s
                """,
                """
                CREATE TEMPORARY TABLESPACE %(tblspace_temp)s
                TEMPFILE '%(datafile_tmp)s' SIZE %(size_tmp)s REUSE
                AUTOEXTEND ON NEXT %(extsize_tmp)s MAXSIZE %(maxsize_tmp)s
                """,
            ]
        # Ignore "tablespace already exists" error when keepdb is on.
        acceptable_ora_err = "ORA-01543" if keepdb else None
        self._execute_allow_fail_statements(
            cursor, statements, parameters, verbosity, acceptable_ora_err
        )