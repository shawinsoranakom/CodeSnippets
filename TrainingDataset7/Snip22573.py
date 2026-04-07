def test_match(self):
        f = FilePathField(path=self.path, match=r"^.*?\.py$")
        self.assertChoices(f, self.expected_choices[:4])