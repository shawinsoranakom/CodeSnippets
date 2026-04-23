def test_pk_validation(self):
        NonAutoPK.objects.create(name="one")
        again = NonAutoPK(name="one")
        with self.assertRaises(ValidationError):
            again.validate_unique()