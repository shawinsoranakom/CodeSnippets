def test_multivalue_field_validation(self):
        def bad_names(value):
            if value == "bad value":
                raise ValidationError("bad value not allowed")

        class NameField(MultiValueField):
            def __init__(self, fields=(), *args, **kwargs):
                fields = (
                    CharField(label="First name", max_length=10),
                    CharField(label="Last name", max_length=10),
                )
                super().__init__(fields=fields, *args, **kwargs)

            def compress(self, data_list):
                return " ".join(data_list)

        class NameForm(Form):
            name = NameField(validators=[bad_names])

        form = NameForm(data={"name": ["bad", "value"]})
        form.full_clean()
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"name": ["bad value not allowed"]})
        form = NameForm(data={"name": ["should be overly", "long for the field names"]})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "name": [
                    "Ensure this value has at most 10 characters (it has 16).",
                    "Ensure this value has at most 10 characters (it has 24).",
                ],
            },
        )
        form = NameForm(data={"name": ["fname", "lname"]})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {"name": "fname lname"})