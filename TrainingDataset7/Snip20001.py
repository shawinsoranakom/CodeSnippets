def _get_csrf_cookie_request(
        self,
        method=None,
        cookie=None,
        post_token=None,
        meta_token=None,
        token_header=None,
        request_class=None,
    ):
        """
        The method argument defaults to "GET". The cookie argument defaults to
        this class's default test cookie. The post_token and meta_token
        arguments are included in the request's req.POST and req.META headers,
        respectively, when that argument is provided and non-None. The
        token_header argument is the header key to use for req.META, defaults
        to "HTTP_X_CSRFTOKEN".
        """
        if cookie is None:
            cookie = self._csrf_id_cookie
        if token_header is None:
            token_header = "HTTP_X_CSRFTOKEN"
        req = self._get_request(
            method=method,
            cookie=cookie,
            request_class=request_class,
        )
        if post_token is not None:
            req.POST["csrfmiddlewaretoken"] = post_token
        if meta_token is not None:
            req.META[token_header] = meta_token
        return req