def _read_csrf_cookie(self, req, resp):
        """
        Return the CSRF cookie as a string, or False if no cookie is present.
        """
        raise NotImplementedError("This method must be implemented by a subclass.")