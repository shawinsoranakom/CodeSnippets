def create_user(self, email, date_of_birth, password=None, **fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email), date_of_birth=date_of_birth, **fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user