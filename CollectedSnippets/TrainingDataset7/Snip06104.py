def get_username(self):
        """Return the username for this User."""
        return getattr(self, self.USERNAME_FIELD)