def test_showmigrations_no_migrations(self):
        out = io.StringIO()
        call_command("showmigrations", stdout=out, no_color=True)
        self.assertEqual("migrations\n (no migrations)\n", out.getvalue().lower())