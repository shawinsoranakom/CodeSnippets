def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        user = self._create_user_object(username, email, password, **extra_fields)
        user.save(using=self._db)
        return user