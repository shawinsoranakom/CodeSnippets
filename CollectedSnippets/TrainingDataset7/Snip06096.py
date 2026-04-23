def configure_user(self, request, user, created=True):
        """
        Configure a user and return the updated user.

        By default, return the user unmodified.
        """
        return user