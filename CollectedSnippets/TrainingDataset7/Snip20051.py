def _set_csrf_cookie(self, req, cookie):
        req.COOKIES[settings.CSRF_COOKIE_NAME] = cookie