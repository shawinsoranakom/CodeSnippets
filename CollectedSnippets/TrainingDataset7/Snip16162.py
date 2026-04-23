def setUpTestData(cls):
        cls.u1 = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )