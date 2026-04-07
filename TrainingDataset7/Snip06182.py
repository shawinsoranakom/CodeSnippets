def save(self, commit=True):
        """Save the new password."""
        return self.set_password_and_save(self.user, commit=commit)