def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@example.com", is_active=False, **cls.user_credentials
        )