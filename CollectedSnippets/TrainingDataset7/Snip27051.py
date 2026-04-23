def test_sqlmigrate_no_operations(self):
        err = io.StringIO()
        call_command("sqlmigrate", "migrations", "0001_initial", stderr=err)
        self.assertEqual(err.getvalue(), "No operations found.\n")