def test_generators_return_none(self, mock_spider):
        def f2():
            yield 1

        def g2():
            yield 1

        def h2():
            yield 1

        def i2():
            yield 1
            yield from generator_that_returns_stuff()

        def j2():
            yield 1

            def helper():
                return 0

            yield helper()

        def k2():
            """
            docstring
            """
            url = """
https://example.org
        """
            yield url

        def l2():
            return

        assert not is_generator_with_return_value(top_level_return_none)
        assert not is_generator_with_return_value(f2)
        assert not is_generator_with_return_value(g2)
        assert not is_generator_with_return_value(h2)
        assert not is_generator_with_return_value(i2)
        assert not is_generator_with_return_value(j2)  # not recursive
        assert not is_generator_with_return_value(k2)  # not recursive
        assert not is_generator_with_return_value(l2)

        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, top_level_return_none)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, f2)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, g2)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, h2)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, i2)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, j2)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, k2)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, l2)
            assert len(w) == 0