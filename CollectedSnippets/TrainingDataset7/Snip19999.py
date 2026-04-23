def _get_cookies_set(self, req, resp):
        """
        Return a list of the cookie values passed to set_cookie() over the
        course of the request-response.
        """
        raise NotImplementedError("This method must be implemented by a subclass.")