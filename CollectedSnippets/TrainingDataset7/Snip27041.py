def test_showmigrations_plan_single_app_label(self):
        """
        `showmigrations --plan app_label` output with a single app_label.
        """
        # Single app with no dependencies on other apps.
        out = io.StringIO()
        call_command("showmigrations", "mutate_state_b", format="plan", stdout=out)
        self.assertEqual(
            "[ ]  mutate_state_b.0001_initial\n[ ]  mutate_state_b.0002_add_field\n",
            out.getvalue(),
        )
        # Single app with dependencies.
        out = io.StringIO()
        call_command("showmigrations", "author_app", format="plan", stdout=out)
        self.assertEqual(
            "[ ]  author_app.0001_initial\n"
            "[ ]  book_app.0001_initial\n"
            "[ ]  author_app.0002_alter_id\n",
            out.getvalue(),
        )
        # Some migrations already applied.
        call_command("migrate", "author_app", "0001", verbosity=0)
        out = io.StringIO()
        call_command("showmigrations", "author_app", format="plan", stdout=out)
        self.assertEqual(
            "[X]  author_app.0001_initial\n"
            "[ ]  book_app.0001_initial\n"
            "[ ]  author_app.0002_alter_id\n",
            out.getvalue(),
        )
        # Cleanup by unmigrating author_app.
        call_command("migrate", "author_app", "zero", verbosity=0)