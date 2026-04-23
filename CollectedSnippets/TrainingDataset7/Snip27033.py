def test_showmigrations_list(self):
        """
        showmigrations --list displays migrations and whether or not they're
        applied.
        """
        out = io.StringIO()
        with mock.patch(
            "django.core.management.color.supports_color", lambda *args: True
        ):
            call_command(
                "showmigrations", format="list", stdout=out, verbosity=0, no_color=False
            )
        self.assertEqual(
            "\x1b[1mmigrations\n\x1b[0m [ ] 0001_initial\n [ ] 0002_second\n",
            out.getvalue().lower(),
        )

        call_command("migrate", "migrations", "0001", verbosity=0)

        out = io.StringIO()
        # Giving the explicit app_label tests for selective `show_list` in the
        # command
        call_command(
            "showmigrations",
            "migrations",
            format="list",
            stdout=out,
            verbosity=0,
            no_color=True,
        )
        self.assertEqual(
            "migrations\n [x] 0001_initial\n [ ] 0002_second\n", out.getvalue().lower()
        )
        out = io.StringIO()
        # Applied datetimes are displayed at verbosity 2+.
        call_command(
            "showmigrations", "migrations", stdout=out, verbosity=2, no_color=True
        )
        migration1 = MigrationRecorder(connection).migration_qs.get(
            app="migrations", name="0001_initial"
        )
        self.assertEqual(
            "migrations\n"
            " [x] 0001_initial (applied at %s)\n"
            " [ ] 0002_second\n" % migration1.applied.strftime("%Y-%m-%d %H:%M:%S"),
            out.getvalue().lower(),
        )
        # Cleanup by unmigrating everything
        call_command("migrate", "migrations", "zero", verbosity=0)