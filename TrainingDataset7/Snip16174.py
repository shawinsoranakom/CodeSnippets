def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="user",
            password="secret",
            email="user@example.com",
            is_staff=True,
        )
        super().setUpTestData()