def setUpTestData(cls):
        cls.staff_user = User.objects.create_user(
            username="staff",
            password="secret",
            email="staff@example.com",
            is_staff=True,
        )
        cls.non_staff_user = User.objects.create_user(
            username="user",
            password="secret",
            email="user@example.com",
            is_staff=False,
        )