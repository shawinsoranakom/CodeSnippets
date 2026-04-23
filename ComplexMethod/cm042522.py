def test_setter_mutable_lazy_loading(self):
        """Mutable attributes are set internally to None only until they are
        read, then they always return the same falsy instance of the
        corresponding mutable structure.

        Setting them to None causes the next read to return a different object.
        """

        response = self.response_class("http://example.com")

        response.request = Request("http://example.com")

        assert response._flags is None
        assert response.flags == []
        assert response.flags is response.flags
        assert response._flags == []
        original_flags = response.flags
        response.flags = None
        assert response._flags is None
        assert response.flags == []
        assert response.flags is not original_flags

        assert response._headers is None
        assert response.headers == {}
        assert response.headers is response.headers
        assert isinstance(response.headers, Headers)
        assert isinstance(response._headers, Headers)
        original_headers = response.headers
        response.headers = None
        assert response._headers is None
        assert response.headers == {}
        assert response._headers == {}
        assert response.headers is not original_headers