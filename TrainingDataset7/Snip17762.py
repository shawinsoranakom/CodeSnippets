def test_case_insensitive_username_custom_user_and_error_message(self):
        class CustomUserCreationForm(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = ExtensionUser
                fields = UserCreationForm.Meta.fields + ("date_of_birth",)
                error_messages = {
                    "username": {"unique": "This username has already been taken."}
                }

        ExtensionUser.objects.create_user(
            username="testclient",
            password="password",
            email="testclient@example.com",
            date_of_birth=datetime.date(1984, 3, 5),
        )
        data = {
            "username": "TeStClIeNt",
            "password1": "test123",
            "password2": "test123",
            "date_of_birth": "1980-01-01",
        }
        form = CustomUserCreationForm(data)
        self.assertIs(form.is_valid(), False)
        self.assertEqual(
            form["username"].errors,
            ["This username has already been taken."],
        )