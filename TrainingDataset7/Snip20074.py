def _read_csrf_cookie(self, req, resp=None):
        """
        Return the CSRF cookie as a string, or False if no cookie is present.
        """
        if CSRF_SESSION_KEY not in req.session:
            return False
        return req.session[CSRF_SESSION_KEY]