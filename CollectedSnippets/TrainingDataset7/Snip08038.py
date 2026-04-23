def exists(self, session_key=None):
        """
        This method makes sense when you're talking to a shared resource, but
        it doesn't matter when you're storing the information in the client's
        cookie.
        """
        return False