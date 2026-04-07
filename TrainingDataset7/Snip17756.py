def test_custom_form(self):
        class CustomUserCreationForm(BaseUserCreationForm):
            class Meta(BaseUserCreationForm.Meta):
                model = ExtensionUser
                fields = UserCreationForm.Meta.fields + ("date_of_birth",)

        data = {
            "username": "testclient",
            "password1": "testclient",
            "password2": "testclient",
            "date_of_birth": "1988-02-24",
        }
        form = CustomUserCreationForm(data)
        self.assertTrue(form.is_valid())