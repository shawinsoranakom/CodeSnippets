def create_superuser(self, username, orgs, password):
        user = self.model(username=username)
        user.set_password(password)
        user.save(using=self._db)
        user.orgs.add(*orgs)
        return user