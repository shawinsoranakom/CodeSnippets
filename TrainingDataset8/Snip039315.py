def test_clear_single_cache(self, _, cache_decorator):
        """It's safe to clear a single function cache from multiple threads."""

        @cache_decorator
        def foo():
            return 42

        # Populate the cache
        foo()

        def clear_foo(_: int) -> None:
            foo.clear()

        # Clear it from a bunch of threads and assert no errors.
        call_on_threads(clear_foo, self.NUM_THREADS)

        # Sanity check: ensure we can still call our cached function.
        self.assertEqual(42, foo())