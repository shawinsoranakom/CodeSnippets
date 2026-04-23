def setUp(self):
        User.objects.create_superuser(username="super", password="secret", email=None)