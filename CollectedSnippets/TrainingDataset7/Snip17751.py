def test_password_extra_validations(self):
        class ExtraValidationForm(ExtraValidationFormMixin, self.form_class):
            def clean_password1(self):
                return self.failing_helper("password1")

            def clean_password2(self):
                return self.failing_helper("password2")

        data = {"username": "extra", "password1": "abc", "password2": "abc"}
        for fields in (["password1"], ["password2"], ["password1", "password2"]):
            with self.subTest(fields=fields):
                errors = {field: [f"Extra validation for {field}."] for field in fields}
                form = ExtraValidationForm(data, failing_fields=errors)
                self.assertIs(form.is_valid(), False)
                self.assertDictEqual(form.errors, errors)