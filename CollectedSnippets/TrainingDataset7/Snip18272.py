def test_custom_error_verbose_name_not_used(self):
        class CustomUserAttributeSimilarityValidator(UserAttributeSimilarityValidator):
            def get_error_message(self):
                return "The password is too close to a user attribute."

        user = User.objects.create_user(
            username="testclient",
            password="password",
            email="testclient@example.com",
            first_name="Test",
            last_name="Client",
        )

        expected_error = "The password is too close to a user attribute."

        with self.assertRaisesMessage(ValidationError, expected_error):
            CustomUserAttributeSimilarityValidator().validate("testclient", user=user)