def test_copy(self):
        """Test Request copy"""

        def somecallback():
            pass

        r1 = self.request_class(
            "http://www.example.com",
            flags=["f1", "f2"],
            callback=somecallback,
            errback=somecallback,
        )
        r1.meta["foo"] = "bar"
        r1.cb_kwargs["key"] = "value"
        r2 = r1.copy()

        # make sure copy does not propagate callbacks
        assert r1.callback is somecallback
        assert r1.errback is somecallback
        assert r2.callback is r1.callback
        assert r2.errback is r2.errback

        # make sure flags list is shallow copied
        assert r1.flags is not r2.flags, "flags must be a shallow copy, not identical"
        assert r1.flags == r2.flags

        # make sure cb_kwargs dict is shallow copied
        assert r1.cb_kwargs is not r2.cb_kwargs, (
            "cb_kwargs must be a shallow copy, not identical"
        )
        assert r1.cb_kwargs == r2.cb_kwargs

        # make sure meta dict is shallow copied
        assert r1.meta is not r2.meta, "meta must be a shallow copy, not identical"
        assert r1.meta == r2.meta

        # make sure headers attribute is shallow copied
        assert r1.headers is not r2.headers, (
            "headers must be a shallow copy, not identical"
        )
        assert r1.headers == r2.headers
        assert r1.encoding == r2.encoding
        assert r1.dont_filter == r2.dont_filter