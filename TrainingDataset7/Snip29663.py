def test_required(self):
        field = SimpleArrayField(forms.CharField(), required=True)
        msg = "This field is required."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean("")