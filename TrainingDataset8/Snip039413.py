def test_multiple_stats(self):
        @st.experimental_memo
        def foo(count):
            return [3.14] * count

        @st.experimental_memo
        def bar():
            return "shivermetimbers"

        foo(1)
        foo(53)
        bar()
        bar()

        foo_cache_name = f"{foo.__module__}.{foo.__qualname__}"
        bar_cache_name = f"{bar.__module__}.{bar.__qualname__}"

        expected = [
            CacheStat(
                category_name="st_memo",
                cache_name=foo_cache_name,
                byte_length=get_byte_length(as_cached_result([3.14])),
            ),
            CacheStat(
                category_name="st_memo",
                cache_name=foo_cache_name,
                byte_length=get_byte_length(as_cached_result([3.14] * 53)),
            ),
            CacheStat(
                category_name="st_memo",
                cache_name=bar_cache_name,
                byte_length=get_byte_length(as_cached_result("shivermetimbers")),
            ),
        ]

        # The order of these is non-deterministic, so check Set equality
        # instead of List equality
        self.assertEqual(set(expected), set(get_memo_stats_provider().get_stats()))