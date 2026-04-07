def create_users(self):
        self.user = CustomPermissionsUser._default_manager.create_user(
            email="test@example.com", password="test", date_of_birth=date(2006, 4, 25)
        )
        self.superuser = CustomPermissionsUser._default_manager.create_superuser(
            email="test2@example.com", password="test", date_of_birth=date(1976, 11, 8)
        )