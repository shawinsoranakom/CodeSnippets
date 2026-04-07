def test_enum_choices_cleans_valid_string(self):
        f = models.CharField(choices=self.Choices, max_length=1)
        self.assertEqual(f.clean("c", None), "c")