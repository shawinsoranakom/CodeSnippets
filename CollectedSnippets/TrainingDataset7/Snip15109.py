def _create_superuser(self, username):
        return User.objects.create_superuser(
            username=username, email="a@b.com", password="xxx"
        )