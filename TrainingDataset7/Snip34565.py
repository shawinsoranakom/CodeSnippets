def setUpTestData(cls):
        cls.u1 = User.objects.create_user(username="testclient", password="password")
        cls.u2 = User.objects.create_user(
            username="inactive", password="password", is_active=False
        )