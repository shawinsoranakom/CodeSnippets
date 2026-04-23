def create(self):
        """
        To create a new key, set the modified flag so that the cookie is set
        on the client for the current request.
        """
        self.modified = True