def test_replace(self):
        super().test_replace()
        r1 = self.response_class(
            url="https://example.org",
            status=200,
            foo="foo",
            bar="bar",
            lost="lost",
        )

        r2 = r1.replace(foo="new-foo", bar="new-bar", lost="new-lost")
        assert isinstance(r2, self.response_class)
        assert r1.foo == "foo"
        assert r1.bar == "bar"
        assert r1.lost == "lost"
        assert r2.foo == "new-foo"
        assert r2.bar == "new-bar"
        assert r2.lost == "new-lost"

        r3 = r1.replace(foo="new-foo", bar="new-bar")
        assert isinstance(r3, self.response_class)
        assert r1.foo == "foo"
        assert r1.bar == "bar"
        assert r1.lost == "lost"
        assert r3.foo == "new-foo"
        assert r3.bar == "new-bar"
        assert r3.lost is None

        r4 = r1.replace(foo="new-foo")
        assert isinstance(r4, self.response_class)
        assert r1.foo == "foo"
        assert r1.bar == "bar"
        assert r1.lost == "lost"
        assert r4.foo == "new-foo"
        assert r4.bar == "bar"
        assert r4.lost is None

        with pytest.raises(
            TypeError,
            match=r"__init__\(\) got an unexpected keyword argument 'unknown'",
        ):
            r1.replace(unknown="unknown")