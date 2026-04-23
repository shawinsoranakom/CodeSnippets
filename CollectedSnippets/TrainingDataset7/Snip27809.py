def test_enum_choices_invalid_input(self):
        f = models.CharField(choices=self.Choices, max_length=1)
        msg = "Value 'a' is not a valid choice."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("a", None)