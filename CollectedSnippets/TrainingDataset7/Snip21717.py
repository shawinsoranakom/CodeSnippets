def setUpTestData(cls):
        cls.u = User.objects.create_user(
            username="fred", password="secret", email="fred@example.com"
        )