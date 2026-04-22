def test_get_cache(self, _, cache_decorator):
        """Accessing a cached value is safe from multiple threads."""

        cached_func_call_count = [0]

        @cache_decorator
        def foo():
            cached_func_call_count[0] += 1
            return 42

        def call_foo(_: int) -> None:
            self.assertEqual(42, foo())

        # Call foo from multiple threads and assert no errors.
        call_on_threads(call_foo, self.NUM_THREADS)