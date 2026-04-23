def test_headers(self):
        # Different ways of setting headers attribute
        url = "http://www.scrapy.org"
        headers = {b"Accept": "gzip", b"Custom-Header": "nothing to tell you"}
        r = self.request_class(url=url, headers=headers)
        p = self.request_class(url=url, headers=r.headers)

        assert r.headers == p.headers
        assert r.headers is not headers
        assert p.headers is not r.headers

        # headers must not be unicode
        h = Headers({"key1": "val1", "key2": "val2"})
        h["newkey"] = "newval"
        for k, v in h.items():
            assert isinstance(k, bytes)
            for s in v:
                assert isinstance(s, bytes)