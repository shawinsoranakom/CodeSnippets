def test_validators_fail(self):
        field = SimpleArrayField(forms.RegexField("[a-e]{2}"))
        msg = "Item 1 in the array did not validate: Enter a valid value."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean("a,bc,de")