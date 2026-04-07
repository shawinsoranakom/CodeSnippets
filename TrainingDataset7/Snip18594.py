def test_create_test_user(self, *mocked_objects):
        creation = DatabaseCreation(connection)
        with mock.patch.object(
            DatabaseCreation, "_test_database_passwd", self._test_database_passwd
        ):
            # Simulate test user creation raising "user already exists"
            with self.patch_execute_statements(self._execute_raise_user_already_exists):
                with mock.patch("builtins.input", return_value="no"):
                    with self.assertRaises(SystemExit):
                        # SystemExit is raised if the user answers "no" to the
                        # prompt asking if it's okay to delete the test user.
                        creation._create_test_db(verbosity=0, keepdb=False)
                # "User already exists" error is ignored when keepdb is on
                creation._create_test_db(verbosity=0, keepdb=True)
            # Simulate test user creation raising unexpected error
            with self.patch_execute_statements(
                self._execute_raise_insufficient_privileges
            ):
                with self.assertRaises(SystemExit):
                    creation._create_test_db(verbosity=0, keepdb=False)
                with self.assertRaises(SystemExit):
                    creation._create_test_db(verbosity=0, keepdb=True)