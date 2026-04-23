def test_return_cached_object(self, _, cache_decorator):
        """If data has been cached, the cache function shouldn't be called."""
        with patch.object(st, "exception") as mock_exception:
            called = [False]

            @cache_decorator
            def f(x):
                called[0] = True
                return x

            self.assertFalse(called[0])
            f(0)

            self.assertTrue(called[0])

            called = [False]  # Reset called

            f(0)
            self.assertFalse(called[0])

            f(1)
            self.assertTrue(called[0])

            mock_exception.assert_not_called()