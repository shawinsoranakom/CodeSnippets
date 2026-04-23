def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", email="a@b.com", password="xxx"
        )