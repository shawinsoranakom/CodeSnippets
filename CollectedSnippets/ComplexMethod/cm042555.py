def test_change_proxy_keep_credentials(self):
        middleware = HttpProxyMiddleware()
        request = Request(
            "https://example.com",
            meta={"proxy": "https://user1:password1@example.com"},
        )
        assert middleware.process_request(request) is None

        request.meta["proxy"] = "https://user1:password1@example.org"
        assert middleware.process_request(request) is None
        assert request.meta["proxy"] == "https://example.org"
        encoded_credentials = middleware._basic_auth_header(
            "user1",
            "password1",
        )
        assert request.headers["Proxy-Authorization"] == b"Basic " + encoded_credentials

        # Make sure, indirectly, that _auth_proxy is updated.
        request.meta["proxy"] = "https://example.com"
        assert middleware.process_request(request) is None
        assert request.meta["proxy"] == "https://example.com"
        assert b"Proxy-Authorization" not in request.headers