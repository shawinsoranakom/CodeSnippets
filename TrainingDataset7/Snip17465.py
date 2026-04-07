def create_superuser(self, email, password, date_of_birth, **fields):
        u = self.create_user(
            email, password=password, date_of_birth=date_of_birth, **fields
        )
        u.is_admin = True
        u.save(using=self._db)
        return u