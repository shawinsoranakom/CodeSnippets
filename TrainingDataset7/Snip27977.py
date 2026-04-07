def test_enum_choices_cleans_valid_string(self):
        f = models.IntegerField(choices=self.Choices)
        self.assertEqual(f.clean("1", None), 1)