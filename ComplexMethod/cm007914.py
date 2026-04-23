def test_mixin(self):
        mixin = self.FakeInstanceStoreMixin()
        assert mixin._get_instance(d={'a': 1, 'b': 2, 'c': {'d', 4}}) == mixin._get_instance(d={'a': 1, 'b': 2, 'c': {'d', 4}})

        assert mixin._get_instance(d={'a': 1, 'b': 2, 'c': {'e', 4}}) != mixin._get_instance(d={'a': 1, 'b': 2, 'c': {'d', 4}})

        assert mixin._get_instance(d={'a': 1, 'b': 2, 'c': {'d', 4}} != mixin._get_instance(d={'a': 1, 'b': 2, 'g': {'d', 4}}))

        assert mixin._get_instance(d={'a': 1}, e=[1, 2, 3]) == mixin._get_instance(d={'a': 1}, e=[1, 2, 3])

        assert mixin._get_instance(d={'a': 1}, e=[1, 2, 3]) != mixin._get_instance(d={'a': 1}, e=[1, 2, 3, 4])

        cookiejar = YoutubeDLCookieJar()
        assert mixin._get_instance(b=[1, 2], c=cookiejar) == mixin._get_instance(b=[1, 2], c=cookiejar)

        assert mixin._get_instance(b=[1, 2], c=cookiejar) != mixin._get_instance(b=[1, 2], c=YoutubeDLCookieJar())

        # Different order
        assert mixin._get_instance(c=cookiejar, b=[1, 2]) == mixin._get_instance(b=[1, 2], c=cookiejar)

        m = mixin._get_instance(t=1234)
        assert mixin._get_instance(t=1234) == m
        mixin._clear_instances()
        assert mixin._get_instance(t=1234) != m