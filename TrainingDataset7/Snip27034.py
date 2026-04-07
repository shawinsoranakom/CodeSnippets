def test_showmigrations_list_squashed(self):
        out = io.StringIO()
        call_command(
            "showmigrations", format="list", stdout=out, verbosity=2, no_color=True
        )
        self.assertEqual(
            "migrations\n [ ] 0001_squashed_0002 (2 squashed migrations)\n",
            out.getvalue().lower(),
        )
        out = io.StringIO()
        call_command(
            "migrate",
            "migrations",
            "0001_squashed_0002",
            stdout=out,
            verbosity=2,
            no_color=True,
        )
        try:
            self.assertIn(
                "operations to perform:\n"
                "  target specific migration: 0001_squashed_0002, from migrations\n"
                "running pre-migrate handlers for application migrations\n"
                "running migrations:\n"
                "  applying migrations.0001_squashed_0002... ok (",
                out.getvalue().lower(),
            )
            out = io.StringIO()
            call_command(
                "showmigrations", format="list", stdout=out, verbosity=2, no_color=True
            )
            self.assertEqual(
                "migrations\n [x] 0001_squashed_0002 (2 squashed migrations)\n",
                out.getvalue().lower(),
            )
        finally:
            # Unmigrate everything.
            call_command("migrate", "migrations", "zero", verbosity=0)