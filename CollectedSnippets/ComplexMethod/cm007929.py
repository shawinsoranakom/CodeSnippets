def test_copy(self):
        req = Request(
            url='http://example.com',
            extensions={'cookiejar': CookieJar()},
            headers={'Accept-Encoding': 'br'},
            proxies={'http': 'http://127.0.0.1'},
            data=[b'123'],
        )
        req_copy = req.copy()
        assert req_copy is not req
        assert req_copy.url == req.url
        assert req_copy.headers == req.headers
        assert req_copy.headers is not req.headers
        assert req_copy.proxies == req.proxies
        assert req_copy.proxies is not req.proxies

        # Data is not able to be copied
        assert req_copy.data == req.data
        assert req_copy.data is req.data

        # Shallow copy extensions
        assert req_copy.extensions is not req.extensions
        assert req_copy.extensions['cookiejar'] == req.extensions['cookiejar']

        # Subclasses are copied by default
        class AnotherRequest(Request):
            pass

        req = AnotherRequest(url='http://127.0.0.1')
        assert isinstance(req.copy(), AnotherRequest)