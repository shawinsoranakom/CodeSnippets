def test_charfield_with_choices_raises_error_on_invalid_choice(self):
        f = models.CharField(choices=[("a", "A"), ("b", "B")])
        msg = "Value 'not a' is not a valid choice."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("not a", None)