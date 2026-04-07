def test_assert_field_output(self):
        error_invalid = ["Enter a valid email address."]
        self.assertFieldOutput(
            EmailField, {"a@a.com": "a@a.com"}, {"aaa": error_invalid}
        )
        with self.assertRaises(AssertionError):
            self.assertFieldOutput(
                EmailField,
                {"a@a.com": "a@a.com"},
                {"aaa": error_invalid + ["Another error"]},
            )
        with self.assertRaises(AssertionError):
            self.assertFieldOutput(
                EmailField, {"a@a.com": "Wrong output"}, {"aaa": error_invalid}
            )
        with self.assertRaises(AssertionError):
            self.assertFieldOutput(
                EmailField,
                {"a@a.com": "a@a.com"},
                {"aaa": ["Come on, gimme some well formatted data, dude."]},
            )