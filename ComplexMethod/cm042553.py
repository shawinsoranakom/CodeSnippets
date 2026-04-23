def test_no_proxy(self):
        os.environ["http_proxy"] = "https://proxy.for.http:3128"
        mw = HttpProxyMiddleware()

        os.environ["no_proxy"] = "*"
        req = Request("http://noproxy.com")
        assert mw.process_request(req) is None
        assert "proxy" not in req.meta

        os.environ["no_proxy"] = "other.com"
        req = Request("http://noproxy.com")
        assert mw.process_request(req) is None
        assert "proxy" in req.meta

        os.environ["no_proxy"] = "other.com,noproxy.com"
        req = Request("http://noproxy.com")
        assert mw.process_request(req) is None
        assert "proxy" not in req.meta

        # proxy from meta['proxy'] takes precedence
        os.environ["no_proxy"] = "*"
        req = Request("http://noproxy.com", meta={"proxy": "http://proxy.com"})
        assert mw.process_request(req) is None
        assert req.meta == {"proxy": "http://proxy.com"}