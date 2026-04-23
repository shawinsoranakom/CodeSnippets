def test_oracle_managed_files(self, *mocked_objects):
        def _execute_capture_statements(
            self, cursor, statements, parameters, verbosity, allow_quiet_fail=False
        ):
            self.tblspace_sqls = statements

        creation = DatabaseCreation(connection)
        # Simulate test database creation with Oracle Managed File (OMF)
        # tablespaces.
        with mock.patch.object(
            DatabaseCreation, "_test_database_oracle_managed_files", return_value=True
        ):
            with self.patch_execute_statements(_execute_capture_statements):
                with connection.cursor() as cursor:
                    creation._execute_test_db_creation(
                        cursor, creation._get_test_db_params(), verbosity=0
                    )
                    tblspace_sql, tblspace_tmp_sql = creation.tblspace_sqls
                    # Datafile names shouldn't appear.
                    self.assertIn("DATAFILE SIZE", tblspace_sql)
                    self.assertIn("TEMPFILE SIZE", tblspace_tmp_sql)
                    # REUSE cannot be used with OMF.
                    self.assertNotIn("REUSE", tblspace_sql)
                    self.assertNotIn("REUSE", tblspace_tmp_sql)