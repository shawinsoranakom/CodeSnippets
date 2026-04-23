def login(self, **credentials):
        """
        Set the Factory to appear as if it has successfully logged into a site.

        Return True if login is possible or False if the provided credentials
        are incorrect.
        """
        from django.contrib.auth import authenticate

        user = authenticate(**credentials)
        if user:
            self._login(user)
            return True
        return False