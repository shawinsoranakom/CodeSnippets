def _get_POST_csrf_cookie_request(
        self,
        cookie=None,
        post_token=None,
        meta_token=None,
        token_header=None,
        request_class=None,
    ):
        return self._get_csrf_cookie_request(
            method="POST",
            cookie=cookie,
            post_token=post_token,
            meta_token=meta_token,
            token_header=token_header,
            request_class=request_class,
        )