def test_regexfield_3(self):
        f = RegexField(re.compile("^[0-9][A-F][0-9]$"))
        self.assertEqual("2A2", f.clean("2A2"))
        self.assertEqual("3F3", f.clean("3F3"))
        with self.assertRaisesMessage(ValidationError, "'Enter a valid value.'"):
            f.clean("3G3")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid value.'"):
            f.clean(" 2A2")
        with self.assertRaisesMessage(ValidationError, "'Enter a valid value.'"):
            f.clean("2A2 ")