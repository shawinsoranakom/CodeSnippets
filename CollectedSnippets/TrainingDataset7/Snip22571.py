def test_no_options(self):
        f = FilePathField(path=self.path)
        expected = [
            ("/filepathfield_test_dir/README", "README"),
        ] + self.expected_choices[:4]
        self.assertChoices(f, expected)