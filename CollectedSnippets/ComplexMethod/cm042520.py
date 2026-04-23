def test_init(self):
        # Response requires url in the constructor
        with pytest.raises(TypeError):
            self.response_class()
        assert isinstance(
            self.response_class("http://example.com/"), self.response_class
        )
        with pytest.raises(TypeError):
            self.response_class(b"http://example.com")
        with pytest.raises(TypeError):
            self.response_class(url="http://example.com", body={})
        # body can be str or None
        assert isinstance(
            self.response_class("http://example.com/", body=b""),
            self.response_class,
        )
        assert isinstance(
            self.response_class("http://example.com/", body=b"body"),
            self.response_class,
        )
        # test presence of all optional parameters
        assert isinstance(
            self.response_class(
                "http://example.com/", body=b"", headers={}, status=200
            ),
            self.response_class,
        )

        r = self.response_class("http://www.example.com")
        assert isinstance(r.url, str)
        assert r.url == "http://www.example.com"
        assert r.status == 200

        assert isinstance(r.headers, Headers)
        assert not r.headers

        headers = {"foo": "bar"}
        body = b"a body"
        r = self.response_class("http://www.example.com", headers=headers, body=body)

        assert r.headers is not headers
        assert r.headers[b"foo"] == b"bar"

        r = self.response_class("http://www.example.com", status=301)
        assert r.status == 301
        r = self.response_class("http://www.example.com", status="301")
        assert r.status == 301
        with pytest.raises(ValueError, match=r"invalid literal for int\(\)"):
            self.response_class("http://example.com", status="lala200")