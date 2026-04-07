def test_subcommands(self):
        "Subcommands can be autocompleted"
        self._user_input("django-admin sql")
        output = self._run_autocomplete()
        self.assertEqual(output, ["sqlflush sqlmigrate sqlsequencereset"])