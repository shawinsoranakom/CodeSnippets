def assertChoices(self, field, expected_choices):
        self.assertEqual(fix_os_paths(field.choices), expected_choices)