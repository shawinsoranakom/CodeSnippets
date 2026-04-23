def url(self, name, force=False):
        """
        Return the non-hashed URL in DEBUG mode.
        """
        return self._url(self.stored_name, name, force)