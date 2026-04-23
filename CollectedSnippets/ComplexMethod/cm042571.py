def test_callback_and_errback(self):
        def a_function():
            pass

        r1 = self.request_class("http://example.com")
        assert r1.callback is None
        assert r1.errback is None

        r2 = self.request_class("http://example.com", callback=a_function)
        assert r2.callback is a_function
        assert r2.errback is None

        r3 = self.request_class("http://example.com", errback=a_function)
        assert r3.callback is None
        assert r3.errback is a_function

        r4 = self.request_class(
            url="http://example.com",
            callback=a_function,
            errback=a_function,
        )
        assert r4.callback is a_function
        assert r4.errback is a_function

        r5 = self.request_class(
            url="http://example.com",
            callback=NO_CALLBACK,
            errback=NO_CALLBACK,
        )
        assert r5.callback is NO_CALLBACK
        assert r5.errback is NO_CALLBACK