def _assert_same_request(self, r1, r2):
        assert r1.__class__ == r2.__class__
        assert r1.url == r2.url
        assert r1.callback == r2.callback
        assert r1.errback == r2.errback
        assert r1.method == r2.method
        assert r1.body == r2.body
        assert r1.headers == r2.headers
        assert r1.cookies == r2.cookies
        assert r1.meta == r2.meta
        assert r1.cb_kwargs == r2.cb_kwargs
        assert r1.encoding == r2.encoding
        assert r1._encoding == r2._encoding
        assert r1.priority == r2.priority
        assert r1.dont_filter == r2.dont_filter
        assert r1.flags == r2.flags
        if isinstance(r1, JsonRequest):
            assert r1.dumps_kwargs == r2.dumps_kwargs