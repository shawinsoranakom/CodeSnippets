def create_users(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )
        self.superuser = User.objects.create_superuser(
            username="test2",
            email="test2@example.com",
            password="test",
        )