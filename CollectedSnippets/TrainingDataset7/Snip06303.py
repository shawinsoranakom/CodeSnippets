async def _acreate_user(self, username, email, password, **extra_fields):
        """See _create_user()"""
        user = self._create_user_object(username, email, password, **extra_fields)
        await user.asave(using=self._db)
        return user