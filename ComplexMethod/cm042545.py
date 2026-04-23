def test_middleware_ignore_schemes(self):
        # http responses are cached by default
        req, res = Request("http://test.com/"), Response("http://test.com/")
        with self._middleware() as mw:
            assert mw.process_request(req) is None
            mw.process_response(req, res)

            cached = mw.process_request(req)
            assert isinstance(cached, Response), type(cached)
            self.assertEqualResponse(res, cached)
            assert "cached" in cached.flags

        # file response is not cached by default
        req, res = Request("file:///tmp/t.txt"), Response("file:///tmp/t.txt")
        with self._middleware() as mw:
            assert mw.process_request(req) is None
            mw.process_response(req, res)

            assert mw.storage.retrieve_response(mw.crawler.spider, req) is None
            assert mw.process_request(req) is None

        # s3 scheme response is cached by default
        req, res = Request("s3://bucket/key"), Response("http://bucket/key")
        with self._middleware() as mw:
            assert mw.process_request(req) is None
            mw.process_response(req, res)

            cached = mw.process_request(req)
            assert isinstance(cached, Response), type(cached)
            self.assertEqualResponse(res, cached)
            assert "cached" in cached.flags

        # ignore s3 scheme
        req, res = Request("s3://bucket/key2"), Response("http://bucket/key2")
        with self._middleware(HTTPCACHE_IGNORE_SCHEMES=["s3"]) as mw:
            assert mw.process_request(req) is None
            mw.process_response(req, res)

            assert mw.storage.retrieve_response(mw.crawler.spider, req) is None
            assert mw.process_request(req) is None