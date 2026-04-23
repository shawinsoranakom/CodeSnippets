async def acreate_user(self, email, date_of_birth, password=None, **fields):
        """See create_user()"""
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email), date_of_birth=date_of_birth, **fields
        )

        user.set_password(password)
        await user.asave(using=self._db)
        return user