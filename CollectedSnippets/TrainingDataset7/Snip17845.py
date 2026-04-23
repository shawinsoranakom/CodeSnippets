def test_no_password_validation_if_unusable_password_set(self):
        data = {
            "username": "otherclient",
            "password1": "otherclient",
            "password2": "otherclient",
            "usable_password": "false",
        }
        form = self.form_class(data)
        # Passwords are not validated if `usable_password` is unset.
        self.assertIs(form.is_valid(), True, form.errors)

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
                "usable_password": "false",
            }
        )
        self.assertIs(form.is_valid(), True, form.errors)