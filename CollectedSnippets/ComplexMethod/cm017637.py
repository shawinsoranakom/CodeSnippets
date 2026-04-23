def _follow_redirect(
        self,
        response,
        *,
        data="",
        content_type="",
        headers=None,
        query_params=None,
        **extra,
    ):
        """Follow a single redirect contained in response using GET."""
        response_url = response.url
        redirect_chain = response.redirect_chain
        redirect_chain.append((response_url, response.status_code))

        url = urlsplit(response_url)
        if url.scheme:
            extra["wsgi.url_scheme"] = url.scheme
        if url.hostname:
            extra["SERVER_NAME"] = url.hostname
            extra["HTTP_HOST"] = url.hostname
        if url.port:
            extra["SERVER_PORT"] = str(url.port)

        path = url.path
        # RFC 3986 Section 6.2.3: Empty path should be normalized to "/".
        if not path and url.netloc:
            path = "/"
        # Prepend the request path to handle relative path redirects
        if not path.startswith("/"):
            path = urljoin(response.request["PATH_INFO"], path)

        if response.status_code in (
            HTTPStatus.TEMPORARY_REDIRECT,
            HTTPStatus.PERMANENT_REDIRECT,
        ):
            # Preserve request method and query string (if needed)
            # post-redirect for 307/308 responses.
            request_method = response.request["REQUEST_METHOD"].lower()
            if request_method not in ("get", "head"):
                extra["QUERY_STRING"] = url.query
            request_method = getattr(self, request_method)
        else:
            request_method = self.get
            data = QueryDict(url.query)
            content_type = None
            query_params = None

        return request_method(
            path,
            data=data,
            content_type=content_type,
            follow=False,
            headers=headers,
            query_params=query_params,
            **extra,
        )