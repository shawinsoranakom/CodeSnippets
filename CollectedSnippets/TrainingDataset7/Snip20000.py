def _get_request(self, method=None, cookie=None, request_class=None):
        if method is None:
            method = "GET"
        if request_class is None:
            request_class = TestingHttpRequest
        req = request_class()
        req.method = method
        if cookie is not None:
            self._set_csrf_cookie(req, cookie)
        return req