def test_remove_credentials(self):
        """If the proxy request meta switches to a proxy URL with the same
        proxy but no credentials, the original credentials must be still
        used.

        To remove credentials while keeping the same proxy URL, users must
        delete the Proxy-Authorization header.
        """
        middleware = HttpProxyMiddleware()
        request = Request(
            "https://example.com",
            meta={"proxy": "https://user1:password1@example.com"},
        )
        assert middleware.process_request(request) is None

        request.meta["proxy"] = "https://example.com"
        assert middleware.process_request(request) is None
        assert request.meta["proxy"] == "https://example.com"
        encoded_credentials = middleware._basic_auth_header(
            "user1",
            "password1",
        )
        assert request.headers["Proxy-Authorization"] == b"Basic " + encoded_credentials

        request.meta["proxy"] = "https://example.com"
        del request.headers[b"Proxy-Authorization"]
        assert middleware.process_request(request) is None
        assert request.meta["proxy"] == "https://example.com"
        assert b"Proxy-Authorization" not in request.headers