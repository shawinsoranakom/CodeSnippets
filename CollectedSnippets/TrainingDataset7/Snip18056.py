def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "test_user", "test@example.com", "test_password"
        )
        cls.user2 = User.objects.create_user(
            "test_user2", "test2@example.com", "test_password2"
        )