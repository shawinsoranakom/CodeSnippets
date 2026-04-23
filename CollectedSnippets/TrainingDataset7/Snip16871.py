def setUp(self):
        self.u1 = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )