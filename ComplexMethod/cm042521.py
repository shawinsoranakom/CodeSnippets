def test_replace(self):
        """Test Response.replace() method"""
        hdrs = Headers({"key": "value"})
        r1 = self.response_class("http://www.example.com")
        r2 = r1.replace(status=301, body=b"New body", headers=hdrs)
        assert r1.body == b""
        assert r1.url == r2.url
        assert (r1.status, r2.status) == (200, 301)
        assert (r1.body, r2.body) == (b"", b"New body")
        assert (r1.headers, r2.headers) == ({}, hdrs)

        # Empty attributes (which may fail if not compared properly)
        r3 = self.response_class("http://www.example.com", flags=["cached"])
        r4 = r3.replace(body=b"", flags=[])
        assert r4.body == b""
        assert not r4.flags