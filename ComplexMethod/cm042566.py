def test_init(self):
        # Request requires url in the __init__ method
        with pytest.raises(TypeError):
            self.request_class()

        # url argument must be basestring
        with pytest.raises(TypeError):
            self.request_class(123)
        r = self.request_class("http://www.example.com")

        r = self.request_class("http://www.example.com")
        assert isinstance(r.url, str)
        assert r.url == "http://www.example.com"
        assert r.method == self.default_method

        assert isinstance(r.headers, Headers)
        assert r.headers == self.default_headers
        assert r.meta == self.default_meta

        meta = {"lala": "lolo"}
        headers = {b"caca": b"coco"}
        r = self.request_class(
            "http://www.example.com", meta=meta, headers=headers, body="a body"
        )

        assert r.meta is not meta
        assert r.meta == meta
        assert r.headers is not headers
        assert r.headers[b"caca"] == b"coco"