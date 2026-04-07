def test_authenticate_user_without_is_active_field(self):
        """
        A custom user without an `is_active` field is allowed to authenticate.
        """
        user = CustomUserWithoutIsActiveField.objects._create_user(
            username="test",
            email="test@example.com",
            password="test",
        )
        self.assertEqual(authenticate(username="test", password="test"), user)