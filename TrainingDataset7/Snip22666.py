def test_regexfield_4(self):
        f = RegexField("^[0-9]+$", min_length=5, max_length=10)
        with self.assertRaisesMessage(
            ValidationError, "'Ensure this value has at least 5 characters (it has 3).'"
        ):
            f.clean("123")
        with self.assertRaisesMessage(
            ValidationError,
            "'Ensure this value has at least 5 characters (it has 3).', "
            "'Enter a valid value.'",
        ):
            f.clean("abc")
        self.assertEqual("12345", f.clean("12345"))
        self.assertEqual("1234567890", f.clean("1234567890"))
        with self.assertRaisesMessage(
            ValidationError,
            "'Ensure this value has at most 10 characters (it has 11).'",
        ):
            f.clean("12345678901")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid value.'"):
            f.clean("12345a")