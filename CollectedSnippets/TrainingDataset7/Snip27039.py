def test_showmigrations_plan_no_migrations(self):
        """
        Tests --plan output of showmigrations command without migrations
        """
        out = io.StringIO()
        call_command("showmigrations", format="plan", stdout=out, no_color=True)
        self.assertEqual("(no migrations)\n", out.getvalue().lower())

        out = io.StringIO()
        call_command(
            "showmigrations", format="plan", stdout=out, verbosity=2, no_color=True
        )
        self.assertEqual("(no migrations)\n", out.getvalue().lower())