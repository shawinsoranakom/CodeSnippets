def test_validate_fail(self):
        field = SimpleArrayField(forms.CharField(required=True))
        msg = "Item 3 in the array did not validate: This field is required."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean("a,b,")