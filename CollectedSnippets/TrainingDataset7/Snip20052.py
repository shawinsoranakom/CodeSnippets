def _read_csrf_cookie(self, req, resp):
        """
        Return the CSRF cookie as a string, or False if no cookie is present.
        """
        if settings.CSRF_COOKIE_NAME not in resp.cookies:
            return False
        csrf_cookie = resp.cookies[settings.CSRF_COOKIE_NAME]
        return csrf_cookie.value