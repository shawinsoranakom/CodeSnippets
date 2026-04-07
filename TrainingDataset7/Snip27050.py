def test_sqlmigrate_replaced_migration(self):
        out = io.StringIO()
        call_command("sqlmigrate", "migrations", "0001_initial", stdout=out)
        output = out.getvalue().lower()
        self.assertIn("-- create model author", output)
        self.assertIn("-- create model tribble", output)