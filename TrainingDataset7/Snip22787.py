def test_has_error(self):
        class UserRegistration(Form):
            username = CharField(max_length=10)
            password1 = CharField(widget=PasswordInput, min_length=5)
            password2 = CharField(widget=PasswordInput)

            def clean(self):
                if (
                    self.cleaned_data.get("password1")
                    and self.cleaned_data.get("password2")
                    and self.cleaned_data["password1"] != self.cleaned_data["password2"]
                ):
                    raise ValidationError(
                        "Please make sure your passwords match.",
                        code="password_mismatch",
                    )

        f = UserRegistration(data={})
        self.assertTrue(f.has_error("password1"))
        self.assertTrue(f.has_error("password1", "required"))
        self.assertFalse(f.has_error("password1", "anything"))

        f = UserRegistration(data={"password1": "Hi", "password2": "Hi"})
        self.assertTrue(f.has_error("password1"))
        self.assertTrue(f.has_error("password1", "min_length"))
        self.assertFalse(f.has_error("password1", "anything"))
        self.assertFalse(f.has_error("password2"))
        self.assertFalse(f.has_error("password2", "anything"))

        f = UserRegistration(data={"password1": "Bonjour", "password2": "Hello"})
        self.assertFalse(f.has_error("password1"))
        self.assertFalse(f.has_error("password1", "required"))
        self.assertTrue(f.has_error(NON_FIELD_ERRORS))
        self.assertTrue(f.has_error(NON_FIELD_ERRORS, "password_mismatch"))
        self.assertFalse(f.has_error(NON_FIELD_ERRORS, "anything"))