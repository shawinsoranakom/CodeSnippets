def _get_POST_request_with_token(self, cookie=None, request_class=None):
        """The cookie argument defaults to this class's default test cookie."""
        return self._get_POST_csrf_cookie_request(
            cookie=cookie,
            post_token=self._csrf_id_token,
            request_class=request_class,
        )