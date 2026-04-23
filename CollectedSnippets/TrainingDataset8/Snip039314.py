def test_clear_all_caches(self, _, cache_decorator, clear_cache_func):
        """Clearing all caches is safe to call from multiple threads."""

        @cache_decorator
        def foo():
            return 42

        # Populate the cache
        foo()

        def clear_caches(_: int) -> None:
            clear_cache_func()

        # Clear the cache from a bunch of threads and assert no errors.
        call_on_threads(clear_caches, self.NUM_THREADS)

        # Sanity check: ensure we can still call our cached function.
        self.assertEqual(42, foo())