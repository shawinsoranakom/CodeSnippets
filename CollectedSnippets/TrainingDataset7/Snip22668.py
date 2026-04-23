def test_change_regex_after_init(self):
        f = RegexField("^[a-z]+$")
        f.regex = "^[0-9]+$"
        self.assertEqual("1234", f.clean("1234"))
        with self.assertRaisesMessage(ValidationError, "'Enter a valid value.'"):
            f.clean("abcd")