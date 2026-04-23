def test_custom_command(self):
        "A custom command can autocomplete option flags"
        self._user_input("django-admin test_command --l")
        output = self._run_autocomplete()
        self.assertEqual(output, ["--list"])