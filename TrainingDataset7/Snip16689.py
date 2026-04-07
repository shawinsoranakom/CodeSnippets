def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.joepublicuser = User.objects.create_user(
            username="joepublic", password="secret"
        )