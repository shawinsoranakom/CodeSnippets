def test_password_changed_with_custom_validator(self):
        class Validator:
            def password_changed(self, password, user):
                self.password = password
                self.user = user

        user = object()
        validator = Validator()
        password_changed("password", user=user, password_validators=(validator,))
        self.assertIs(validator.user, user)
        self.assertEqual(validator.password, "password")