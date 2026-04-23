def test_generators_return_none_with_decorator(self, mock_spider):  # noqa: PLR0915
        def decorator(func):
            def inner_func():
                func()

            return inner_func

        @decorator
        def f3():
            yield 1

        @decorator
        def g3():
            yield 1

        @decorator
        def h3():
            yield 1

        @decorator
        def i3():
            yield 1
            yield from generator_that_returns_stuff()

        @decorator
        def j3():
            yield 1

            def helper():
                return 0

            yield helper()

        @decorator
        def k3():
            """
            docstring
            """
            url = """
https://example.org
        """
            yield url

        @decorator
        def l3():
            return

        assert not is_generator_with_return_value(top_level_return_none)
        assert not is_generator_with_return_value(f3)
        assert not is_generator_with_return_value(g3)
        assert not is_generator_with_return_value(h3)
        assert not is_generator_with_return_value(i3)
        assert not is_generator_with_return_value(j3)  # not recursive
        assert not is_generator_with_return_value(k3)  # not recursive
        assert not is_generator_with_return_value(l3)

        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, top_level_return_none)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, f3)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, g3)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, h3)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, i3)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, j3)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, k3)
            assert len(w) == 0
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, l3)
            assert len(w) == 0