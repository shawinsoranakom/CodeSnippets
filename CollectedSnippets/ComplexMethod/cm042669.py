def _build_redirect_request(
        self, source_request: Request, response: Response, *, url: str, **kwargs: Any
    ) -> Request:
        redirect_request = source_request.replace(
            url=url,
            **kwargs,
            cls=None,
            cookies=None,
        )
        if "_scheme_proxy" in redirect_request.meta:
            source_request_scheme = urlparse_cached(source_request).scheme
            redirect_request_scheme = urlparse_cached(redirect_request).scheme
            if source_request_scheme != redirect_request_scheme:
                redirect_request.meta.pop("_scheme_proxy")
                redirect_request.meta.pop("proxy", None)
                redirect_request.meta.pop("_auth_proxy", None)
                redirect_request.headers.pop(b"Proxy-Authorization", None)

        has_cookie_header = "Cookie" in redirect_request.headers
        has_authorization_header = "Authorization" in redirect_request.headers
        if has_cookie_header or has_authorization_header:
            default_ports = {"http": 80, "https": 443}

            parsed_source_request = urlparse_cached(source_request)
            source_scheme, source_host, source_port = (
                parsed_source_request.scheme,
                parsed_source_request.hostname,
                parsed_source_request.port
                or default_ports.get(parsed_source_request.scheme),
            )

            parsed_redirect_request = urlparse_cached(redirect_request)
            redirect_scheme, redirect_host, redirect_port = (
                parsed_redirect_request.scheme,
                parsed_redirect_request.hostname,
                parsed_redirect_request.port
                or default_ports.get(parsed_redirect_request.scheme),
            )

            if has_cookie_header and (
                redirect_scheme not in {source_scheme, "https"}
                or source_host != redirect_host
            ):
                del redirect_request.headers["Cookie"]

            # https://fetch.spec.whatwg.org/#ref-for-cors-non-wildcard-request-header-name
            if has_authorization_header and (
                source_scheme != redirect_scheme
                or source_host != redirect_host
                or source_port != redirect_port
            ):
                del redirect_request.headers["Authorization"]

        self.handle_referer(redirect_request, response)

        return redirect_request