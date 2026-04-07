def test_custom_form_with_different_username_field(self):
        class CustomUserCreationForm(BaseUserCreationForm):
            class Meta(BaseUserCreationForm.Meta):
                model = CustomUser
                fields = ("email", "date_of_birth")

        data = {
            "email": "test@client222.com",
            "password1": "testclient",
            "password2": "testclient",
            "date_of_birth": "1988-02-24",
        }
        form = CustomUserCreationForm(data)
        self.assertTrue(form.is_valid())