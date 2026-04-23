def test_response_cacheability(self):
        responses = [
            # 304 is not cacheable no matter what servers sends
            (False, 304, {}),
            (False, 304, {"Last-Modified": self.yesterday}),
            (False, 304, {"Expires": self.tomorrow}),
            (False, 304, {"Etag": "bar"}),
            (False, 304, {"Cache-Control": "max-age=3600"}),
            # Always obey no-store cache control
            (False, 200, {"Cache-Control": "no-store"}),
            (False, 200, {"Cache-Control": "no-store, max-age=300"}),  # invalid
            (
                False,
                200,
                {"Cache-Control": "no-store", "Expires": self.tomorrow},
            ),  # invalid
            # Ignore responses missing expiration and/or validation headers
            (False, 200, {}),
            (False, 302, {}),
            (False, 307, {}),
            (False, 404, {}),
            # Cache responses with expiration and/or validation headers
            (True, 200, {"Last-Modified": self.yesterday}),
            (True, 203, {"Last-Modified": self.yesterday}),
            (True, 300, {"Last-Modified": self.yesterday}),
            (True, 301, {"Last-Modified": self.yesterday}),
            (True, 308, {"Last-Modified": self.yesterday}),
            (True, 401, {"Last-Modified": self.yesterday}),
            (True, 404, {"Cache-Control": "public, max-age=600"}),
            (True, 302, {"Expires": self.tomorrow}),
            (True, 200, {"Etag": "foo"}),
        ]
        with self._middleware() as mw:
            for idx, (shouldcache, status, headers) in enumerate(responses):
                req0 = Request(f"http://example-{idx}.com")
                res0 = Response(req0.url, status=status, headers=headers)
                res1 = self._process_requestresponse(mw, req0, res0)
                res304 = res0.replace(status=304)
                res2 = self._process_requestresponse(
                    mw, req0, res304 if shouldcache else res0
                )
                self.assertEqualResponse(res1, res0)
                self.assertEqualResponse(res2, res0)
                resc = mw.storage.retrieve_response(mw.crawler.spider, req0)
                if shouldcache:
                    self.assertEqualResponse(resc, res1)
                    assert "cached" in res2.flags
                    assert res2.status != 304
                else:
                    assert not resc
                    assert "cached" not in res2.flags

        # cache unconditionally unless response contains no-store or is a 304
        with self._middleware(HTTPCACHE_ALWAYS_STORE=True) as mw:
            for idx, (_, status, headers) in enumerate(responses):
                shouldcache = (
                    "no-store" not in headers.get("Cache-Control", "") and status != 304
                )
                req0 = Request(f"http://example2-{idx}.com")
                res0 = Response(req0.url, status=status, headers=headers)
                res1 = self._process_requestresponse(mw, req0, res0)
                res304 = res0.replace(status=304)
                res2 = self._process_requestresponse(
                    mw, req0, res304 if shouldcache else res0
                )
                self.assertEqualResponse(res1, res0)
                self.assertEqualResponse(res2, res0)
                resc = mw.storage.retrieve_response(mw.crawler.spider, req0)
                if shouldcache:
                    self.assertEqualResponse(resc, res1)
                    assert "cached" in res2.flags
                    assert res2.status != 304
                else:
                    assert not resc
                    assert "cached" not in res2.flags