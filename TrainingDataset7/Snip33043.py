def test_value_error(self):
        self.assertEqual(pluralize("", "y,es"), "")
        self.assertEqual(pluralize("", "es"), "")