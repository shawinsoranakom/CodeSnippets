def setUpTestData(cls):
        cls.u1 = User.objects.create_user(
            username="testclient", password="password", email="testclient@example.com"
        )
        cls.u2 = User.objects.create_user(
            username="inactive", password="password", is_active=False
        )
        cls.u3 = User.objects.create_user(username="staff", password="password")
        cls.u4 = User.objects.create(username="empty_password", password="")
        cls.u5 = User.objects.create(username="unmanageable_password", password="$")
        cls.u6 = User.objects.create(username="unknown_password", password="foo$bar")
        cls.u7 = User.objects.create(
            username="unusable_password", password=make_password(None)
        )