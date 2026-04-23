def _set_csrf_cookie(self, req, cookie):
        req.session[CSRF_SESSION_KEY] = cookie