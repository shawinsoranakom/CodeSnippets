def test_custom_form_hidden_username_field(self):
        class CustomUserCreationForm(BaseUserCreationForm):
            class Meta(BaseUserCreationForm.Meta):
                model = CustomUserWithoutIsActiveField
                fields = ("email",)  # without USERNAME_FIELD

        data = {
            "email": "testclient@example.com",
            "password1": "testclient",
            "password2": "testclient",
        }
        form = CustomUserCreationForm(data)
        self.assertTrue(form.is_valid())