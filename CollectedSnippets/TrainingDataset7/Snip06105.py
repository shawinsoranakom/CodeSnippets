def clean(self):
        setattr(self, self.USERNAME_FIELD, self.normalize_username(self.get_username()))