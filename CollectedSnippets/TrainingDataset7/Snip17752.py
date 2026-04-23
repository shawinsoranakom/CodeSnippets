def test_user_create_form_validates_password_with_all_data(self):
        """
        BaseUserCreationForm password validation uses all of the form's data.
        """

        class CustomUserCreationForm(self.form_class):
            class Meta(self.form_class.Meta):
                model = User
                fields = ("username", "email", "first_name", "last_name")

        form = CustomUserCreationForm(
            {
                "username": "testuser",
                "password1": "testpassword",
                "password2": "testpassword",
                "first_name": "testpassword",
                "last_name": "lastname",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["password2"],
            ["The password is too similar to the first name."],
        )