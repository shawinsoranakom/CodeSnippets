def test_cached_and_stale(self):
        sampledata = [
            (200, {"Date": self.today, "Expires": self.yesterday}),
            (
                200,
                {
                    "Date": self.today,
                    "Expires": self.yesterday,
                    "Last-Modified": self.yesterday,
                },
            ),
            (200, {"Expires": self.yesterday}),
            (200, {"Expires": self.yesterday, "ETag": "foo"}),
            (200, {"Expires": self.yesterday, "Last-Modified": self.yesterday}),
            (200, {"Expires": self.tomorrow, "Age": "86405"}),
            (200, {"Cache-Control": "max-age=86400", "Age": "86405"}),
            # no-cache forces expiration, also revalidation if validators exists
            (200, {"Cache-Control": "no-cache"}),
            (200, {"Cache-Control": "no-cache", "ETag": "foo"}),
            (200, {"Cache-Control": "no-cache", "Last-Modified": self.yesterday}),
            (
                200,
                {
                    "Cache-Control": "no-cache,must-revalidate",
                    "Last-Modified": self.yesterday,
                },
            ),
            (
                200,
                {
                    "Cache-Control": "must-revalidate",
                    "Expires": self.yesterday,
                    "Last-Modified": self.yesterday,
                },
            ),
            (200, {"Cache-Control": "max-age=86400,must-revalidate", "Age": "86405"}),
        ]
        with self._middleware() as mw:
            for idx, (status, headers) in enumerate(sampledata):
                req0 = Request(f"http://example-{idx}.com")
                res0a = Response(req0.url, status=status, headers=headers)
                # cache expired response
                res1 = self._process_requestresponse(mw, req0, res0a)
                self.assertEqualResponse(res1, res0a)
                assert "cached" not in res1.flags
                # Same request but as cached response is stale a new response must
                # be returned
                res0b = res0a.replace(body=b"bar")
                res2 = self._process_requestresponse(mw, req0, res0b)
                self.assertEqualResponse(res2, res0b)
                assert "cached" not in res2.flags
                cc = headers.get("Cache-Control", "")
                # Previous response expired too, subsequent request to same
                # resource must revalidate and succeed on 304 if validators
                # are present
                if "ETag" in headers or "Last-Modified" in headers:
                    res0c = res0b.replace(status=304)
                    res3 = self._process_requestresponse(mw, req0, res0c)
                    self.assertEqualResponse(res3, res0b)
                    assert "cached" in res3.flags
                    # get cached response on server errors unless must-revalidate
                    # in cached response
                    res0d = res0b.replace(status=500)
                    res4 = self._process_requestresponse(mw, req0, res0d)
                    if "must-revalidate" in cc:
                        assert "cached" not in res4.flags
                        self.assertEqualResponse(res4, res0d)
                    else:
                        assert "cached" in res4.flags
                        self.assertEqualResponse(res4, res0b)
                # Requests with max-stale can fetch expired cached responses
                # unless cached response has must-revalidate
                req1 = req0.replace(headers={"Cache-Control": "max-stale"})
                res5 = self._process_requestresponse(mw, req1, res0b)
                self.assertEqualResponse(res5, res0b)
                if "no-cache" in cc or "must-revalidate" in cc:
                    assert "cached" not in res5.flags
                else:
                    assert "cached" in res5.flags