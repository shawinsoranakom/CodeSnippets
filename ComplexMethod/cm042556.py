def test_proxy_authentication_header_proxy_without_credentials(self):
        """As long as the proxy URL in request metadata remains the same, the
        Proxy-Authorization header is used and kept, and may even be
        changed."""
        middleware = HttpProxyMiddleware()
        request = Request(
            "https://example.com",
            headers={"Proxy-Authorization": "Basic foo"},
            meta={"proxy": "https://example.com"},
        )
        assert middleware.process_request(request) is None
        assert request.meta["proxy"] == "https://example.com"
        assert request.headers["Proxy-Authorization"] == b"Basic foo"

        assert middleware.process_request(request) is None
        assert request.meta["proxy"] == "https://example.com"
        assert request.headers["Proxy-Authorization"] == b"Basic foo"

        request.headers["Proxy-Authorization"] = b"Basic bar"
        assert middleware.process_request(request) is None
        assert request.meta["proxy"] == "https://example.com"
        assert request.headers["Proxy-Authorization"] == b"Basic bar"