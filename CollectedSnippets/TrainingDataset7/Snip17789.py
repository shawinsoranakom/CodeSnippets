def test_password_extra_validations(self):
        class ExtraValidationForm(ExtraValidationFormMixin, SetPasswordForm):
            def clean_new_password1(self):
                return self.failing_helper("new_password1")

            def clean_new_password2(self):
                return self.failing_helper("new_password2")

        user = User.objects.get(username="testclient")
        data = {"new_password1": "abc", "new_password2": "abc"}
        for fields in (
            ["new_password1"],
            ["new_password2"],
            ["new_password1", "new_password2"],
        ):
            with self.subTest(fields=fields):
                errors = {field: [f"Extra validation for {field}."] for field in fields}
                form = ExtraValidationForm(user, data, failing_fields=errors)
                self.assertIs(form.is_valid(), False)
                self.assertDictEqual(form.errors, errors)