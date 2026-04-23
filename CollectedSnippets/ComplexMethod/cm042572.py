def test_setter_mutable_lazy_loading(self):
        """Mutable attributes are set internally to None only until they are
        read, then they always return the same falsy instance of the
        corresponding mutable structure.

        Setting them to None causes the next read to return a different object.
        """

        request = self.request_class("http://example.com")

        assert request._flags is None
        assert request.flags == []
        assert request.flags is request.flags
        assert request._flags == []
        original_flags = request.flags
        request.flags = None
        assert request._flags is None
        assert request.flags == []
        assert request.flags is not original_flags

        assert request._cookies is None
        assert request.cookies == {}
        assert request.cookies is request.cookies
        assert request._cookies == {}
        original_cookies = request.cookies
        request.cookies = None
        assert request._cookies is None
        assert request.cookies == {}
        assert request.cookies is not original_cookies

        if self.default_headers:
            assert request._headers == self.default_headers
            assert request._headers is not self.default_headers
            assert request.headers == self.default_headers
        else:
            assert request._headers is None
            assert request.headers == {}
        assert request.headers is request.headers
        assert isinstance(request.headers, Headers)
        assert isinstance(request._headers, Headers)
        original_headers = request.headers
        request.headers = None
        assert request._headers is None
        assert request.headers == {}
        assert request._headers == {}
        assert request.headers is not original_headers