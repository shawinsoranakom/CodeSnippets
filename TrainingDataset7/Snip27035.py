def test_showmigrations_plan(self):
        """
        Tests --plan output of showmigrations command
        """
        out = io.StringIO()
        call_command("showmigrations", format="plan", stdout=out)
        self.assertEqual(
            "[ ]  migrations.0001_initial\n"
            "[ ]  migrations.0003_third\n"
            "[ ]  migrations.0002_second\n",
            out.getvalue().lower(),
        )

        out = io.StringIO()
        call_command("showmigrations", format="plan", stdout=out, verbosity=2)
        self.assertEqual(
            "[ ]  migrations.0001_initial\n"
            "[ ]  migrations.0003_third ... (migrations.0001_initial)\n"
            "[ ]  migrations.0002_second ... (migrations.0001_initial, "
            "migrations.0003_third)\n",
            out.getvalue().lower(),
        )
        call_command("migrate", "migrations", "0003", verbosity=0)

        out = io.StringIO()
        call_command("showmigrations", format="plan", stdout=out)
        self.assertEqual(
            "[x]  migrations.0001_initial\n"
            "[x]  migrations.0003_third\n"
            "[ ]  migrations.0002_second\n",
            out.getvalue().lower(),
        )

        out = io.StringIO()
        call_command("showmigrations", format="plan", stdout=out, verbosity=2)
        self.assertEqual(
            "[x]  migrations.0001_initial\n"
            "[x]  migrations.0003_third ... (migrations.0001_initial)\n"
            "[ ]  migrations.0002_second ... (migrations.0001_initial, "
            "migrations.0003_third)\n",
            out.getvalue().lower(),
        )

        # Cleanup by unmigrating everything
        call_command("migrate", "migrations", "zero", verbosity=0)