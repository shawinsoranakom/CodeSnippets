def test_replace(self):
        """Test Request.replace() method"""
        r1 = self.request_class("http://www.example.com", method="GET")
        hdrs = Headers(r1.headers)
        hdrs[b"key"] = b"value"
        r2 = r1.replace(method="POST", body="New body", headers=hdrs)
        assert r1.url == r2.url
        assert (r1.method, r2.method) == ("GET", "POST")
        assert (r1.body, r2.body) == (b"", b"New body")
        assert (r1.headers, r2.headers) == (self.default_headers, hdrs)

        # Empty attributes (which may fail if not compared properly)
        r3 = self.request_class(
            "http://www.example.com", meta={"a": 1}, dont_filter=True
        )
        r4 = r3.replace(
            url="http://www.example.com/2", body=b"", meta={}, dont_filter=False
        )
        assert r4.url == "http://www.example.com/2"
        assert r4.body == b""
        assert r4.meta == {}
        assert r4.dont_filter is False