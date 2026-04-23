def create_users(self):
        self.user = ExtensionUser._default_manager.create_user(
            username="test",
            email="test@example.com",
            password="test",
            date_of_birth=date(2006, 4, 25),
        )
        self.superuser = ExtensionUser._default_manager.create_superuser(
            username="test2",
            email="test2@example.com",
            password="test",
            date_of_birth=date(1976, 11, 8),
        )