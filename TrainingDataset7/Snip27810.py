def test_charfield_raises_error_on_empty_input(self):
        f = models.CharField(null=False)
        msg = "This field cannot be null."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(None, None)