def setUpTestData(cls):
        cls.enterClassContext(translation.override(None))
        cls.u1 = User.objects.create_user(
            password="secret",
            last_login=datetime.datetime(2007, 5, 30, 13, 20, 10, tzinfo=UTC),
            is_superuser=True,
            username="super",
            first_name="Super",
            last_name="User",
            email="super@example.com",
            is_staff=True,
            is_active=True,
            date_joined=datetime.datetime(2007, 5, 30, 13, 20, 10, tzinfo=UTC),
        )