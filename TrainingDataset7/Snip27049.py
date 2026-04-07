def test_sqlmigrate_squashed_migration(self):
        out = io.StringIO()
        call_command("sqlmigrate", "migrations", "0001_squashed_0002", stdout=out)
        output = out.getvalue().lower()
        self.assertIn("-- create model author", output)
        self.assertIn("-- create model book", output)
        self.assertNotIn("-- create model tribble", output)