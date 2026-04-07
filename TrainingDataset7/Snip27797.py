def test_boolean_field_doesnt_accept_empty_input(self):
        f = models.BooleanField()
        with self.assertRaises(ValidationError):
            f.clean(None, None)