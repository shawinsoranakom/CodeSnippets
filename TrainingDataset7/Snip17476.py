def create_superuser(self, username=None, **extra_fields):
        return self._create_user(username, **extra_fields)