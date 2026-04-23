def test_proxy_auth_encoding(self):
        # utf-8 encoding
        os.environ["http_proxy"] = "https://m\u00e1n:pass@proxy:3128"
        mw = HttpProxyMiddleware(auth_encoding="utf-8")
        req = Request("http://scrapytest.org")
        assert mw.process_request(req) is None
        assert req.meta["proxy"] == "https://proxy:3128"
        assert req.headers.get("Proxy-Authorization") == b"Basic bcOhbjpwYXNz"

        # proxy from request.meta
        req = Request(
            "http://scrapytest.org", meta={"proxy": "https://\u00fcser:pass@proxy:3128"}
        )
        assert mw.process_request(req) is None
        assert req.meta["proxy"] == "https://proxy:3128"
        assert req.headers.get("Proxy-Authorization") == b"Basic w7xzZXI6cGFzcw=="

        # default latin-1 encoding
        mw = HttpProxyMiddleware(auth_encoding="latin-1")
        req = Request("http://scrapytest.org")
        assert mw.process_request(req) is None
        assert req.meta["proxy"] == "https://proxy:3128"
        assert req.headers.get("Proxy-Authorization") == b"Basic beFuOnBhc3M="

        # proxy from request.meta, latin-1 encoding
        req = Request(
            "http://scrapytest.org", meta={"proxy": "https://\u00fcser:pass@proxy:3128"}
        )
        assert mw.process_request(req) is None
        assert req.meta["proxy"] == "https://proxy:3128"
        assert req.headers.get("Proxy-Authorization") == b"Basic /HNlcjpwYXNz"