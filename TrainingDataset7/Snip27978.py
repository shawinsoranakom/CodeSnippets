def test_enum_choices_invalid_input(self):
        f = models.IntegerField(choices=self.Choices)
        with self.assertRaises(ValidationError):
            f.clean("A", None)
        with self.assertRaises(ValidationError):
            f.clean("3", None)