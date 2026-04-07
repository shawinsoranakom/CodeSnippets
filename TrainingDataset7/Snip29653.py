def test_to_python_fail(self):
        field = SimpleArrayField(forms.IntegerField())
        msg = "Item 1 in the array did not validate: Enter a whole number."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean("a,b,9")