def save(self, commit=True):
        return self.set_password_and_save(self.user, "new_password1", commit=commit)