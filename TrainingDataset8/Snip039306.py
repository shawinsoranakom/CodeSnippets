def test_clear_all_caches(self, _, cache_decorator, clear_cache_func):
        """Calling a cache's global `clear_all` function should remove all
        items from all caches of the appropriate type.
        """
        foo_vals = []

        @cache_decorator
        def foo(x):
            foo_vals.append(x)
            return x

        bar_vals = []

        @cache_decorator
        def bar(x):
            bar_vals.append(x)
            return x

        foo(0), foo(1), foo(2)
        bar(0), bar(1), bar(2)
        self.assertEqual([0, 1, 2], foo_vals)
        self.assertEqual([0, 1, 2], bar_vals)

        # Clear the cache and access our original values again. They
        # should be recomputed.
        clear_cache_func()

        foo(0), foo(1), foo(2)
        bar(0), bar(1), bar(2)
        self.assertEqual([0, 1, 2, 0, 1, 2], foo_vals)
        self.assertEqual([0, 1, 2, 0, 1, 2], bar_vals)