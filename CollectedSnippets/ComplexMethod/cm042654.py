def test_generators_return_something(self, mock_spider):
        def f1():
            yield 1
            return 2

        def g1():
            yield 1
            return "asdf"

        def h1():
            yield 1

            def helper():
                return 0

            yield helper()
            return 2

        def i1():
            """
            docstring
            """
            url = """
https://example.org
        """
            yield url
            return 1

        assert is_generator_with_return_value(top_level_return_something)
        assert is_generator_with_return_value(f1)
        assert is_generator_with_return_value(g1)
        assert is_generator_with_return_value(h1)
        assert is_generator_with_return_value(i1)

        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, top_level_return_something)
            assert len(w) == 1
            assert (
                'The "MockSpider.top_level_return_something" method is a generator'
                in str(w[0].message)
            )
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, f1)
            assert len(w) == 1
            assert 'The "MockSpider.f1" method is a generator' in str(w[0].message)
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, g1)
            assert len(w) == 1
            assert 'The "MockSpider.g1" method is a generator' in str(w[0].message)
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, h1)
            assert len(w) == 1
            assert 'The "MockSpider.h1" method is a generator' in str(w[0].message)
        with warnings.catch_warnings(record=True) as w:
            warn_on_generator_with_return_value(mock_spider, i1)
            assert len(w) == 1
            assert 'The "MockSpider.i1" method is a generator' in str(w[0].message)