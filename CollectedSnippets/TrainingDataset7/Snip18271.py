def test_custom_error(self):
        class CustomUserAttributeSimilarityValidator(UserAttributeSimilarityValidator):
            def get_error_message(self):
                return "The password is too close to the %(verbose_name)s."

        user = User.objects.create_user(
            username="testclient",
            password="password",
            email="testclient@example.com",
            first_name="Test",
            last_name="Client",
        )

        expected_error = "The password is too close to the %s."

        with self.assertRaisesMessage(ValidationError, expected_error % "username"):
            CustomUserAttributeSimilarityValidator().validate("testclient", user=user)