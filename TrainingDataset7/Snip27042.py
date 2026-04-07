def test_showmigrations_plan_multiple_app_labels(self):
        """
        `showmigrations --plan app_label` output with multiple app_labels.
        """
        # Multiple apps: author_app depends on book_app; mutate_state_b doesn't
        # depend on other apps.
        out = io.StringIO()
        call_command(
            "showmigrations", "mutate_state_b", "author_app", format="plan", stdout=out
        )
        self.assertEqual(
            "[ ]  author_app.0001_initial\n"
            "[ ]  book_app.0001_initial\n"
            "[ ]  author_app.0002_alter_id\n"
            "[ ]  mutate_state_b.0001_initial\n"
            "[ ]  mutate_state_b.0002_add_field\n",
            out.getvalue(),
        )
        # Multiple apps: args order shouldn't matter (the same result is
        # expected as above).
        out = io.StringIO()
        call_command(
            "showmigrations", "author_app", "mutate_state_b", format="plan", stdout=out
        )
        self.assertEqual(
            "[ ]  author_app.0001_initial\n"
            "[ ]  book_app.0001_initial\n"
            "[ ]  author_app.0002_alter_id\n"
            "[ ]  mutate_state_b.0001_initial\n"
            "[ ]  mutate_state_b.0002_add_field\n",
            out.getvalue(),
        )