def test_charfield_raises_error_on_empty_string(self):
        f = models.CharField()
        msg = "This field cannot be blank."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("", None)