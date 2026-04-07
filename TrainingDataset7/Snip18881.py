def test_help(self):
        "No errors, just an empty list if there are no autocomplete options"
        self._user_input("django-admin help --")
        output = self._run_autocomplete()
        self.assertEqual(output, [""])