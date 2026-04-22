def test_simple(self, _, cache_decorator):
        @cache_decorator
        def foo():
            return 42

        self.assertEqual(foo(), 42)
        self.assertEqual(foo(), 42)