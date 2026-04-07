def test_regexfield_2(self):
        f = RegexField("^[0-9][A-F][0-9]$", required=False)
        self.assertEqual("2A2", f.clean("2A2"))
        self.assertEqual("3F3", f.clean("3F3"))
        with self.assertRaisesMessage(ValidationError, "'Enter a valid value.'"):
            f.clean("3G3")
        self.assertEqual("", f.clean(""))