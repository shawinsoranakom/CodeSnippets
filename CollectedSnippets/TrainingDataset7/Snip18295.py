def setUpTestData(cls):
        cls.u1 = User.objects.create_user(
            username="testclient", password="password", email="testclient@example.com"
        )
        cls.u3 = User.objects.create_user(
            username="staff", password="password", email="staffmember@example.com"
        )