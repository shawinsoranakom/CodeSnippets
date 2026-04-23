def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", email="super@example.com", password="secret"
        )