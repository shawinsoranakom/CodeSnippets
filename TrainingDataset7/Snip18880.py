def test_completed_subcommand(self):
        "Show option flags in case a subcommand is completed"
        self._user_input("django-admin startproject ")  # Trailing whitespace
        output = self._run_autocomplete()
        for item in output:
            self.assertTrue(item.startswith("--"))