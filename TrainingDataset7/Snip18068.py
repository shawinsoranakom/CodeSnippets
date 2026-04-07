def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "test_user", "test@example.com", "test_password"
        )