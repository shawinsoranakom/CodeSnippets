def setUpTestData(cls):
        cls.test_user = User.objects.create_user(
            "testuser", "test@example.com", "testpw"
        )