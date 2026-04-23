def test_create_test_db_database_exists(self, *mocked_objects):
        # Simulate test database creation raising "database exists"
        creation = DatabaseCreation(connection)
        with self.patch_test_db_creation(self._execute_raise_database_exists):
            with mock.patch("builtins.input", return_value="no"):
                with self.assertRaises(SystemExit):
                    # SystemExit is raised if the user answers "no" to the
                    # prompt asking if it's okay to delete the test database.
                    creation._create_test_db(
                        verbosity=0, autoclobber=False, keepdb=False
                    )
            # "Database exists" shouldn't appear when keepdb is on
            creation._create_test_db(verbosity=0, autoclobber=False, keepdb=True)