def _create_user(self, username, **extra_fields):
        user = self.model(username=username, **extra_fields)
        user.save(using=self._db)
        return user