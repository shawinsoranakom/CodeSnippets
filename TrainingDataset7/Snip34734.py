def setUpTestData(cls):
        cls.u1 = User.objects.create_user(username="testclient", password="password")
        cls.staff = User.objects.create_user(
            username="staff", password="password", is_staff=True
        )