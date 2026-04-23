def test_clone_test_db_database_exists(self):
        creation = DatabaseCreation(connection)
        with self.patch_test_db_creation(self._execute_raise_database_exists):
            with mock.patch.object(DatabaseCreation, "_clone_db") as _clone_db:
                creation._clone_test_db("suffix", verbosity=0, keepdb=True)
                _clone_db.assert_not_called()