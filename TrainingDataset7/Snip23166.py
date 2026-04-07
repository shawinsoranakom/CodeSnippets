def test_field_validators_can_be_any_iterable(self):
        class UserForm(forms.Form):
            full_name = forms.CharField(
                max_length=50,
                validators=(
                    validators.validate_integer,
                    validators.validate_email,
                ),
            )

        form = UserForm({"full_name": "not int nor mail"})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["full_name"],
            ["Enter a valid integer.", "Enter a valid email address."],
        )