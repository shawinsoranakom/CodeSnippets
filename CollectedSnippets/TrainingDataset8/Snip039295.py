def test_mutate_args(self, _, cache_decorator):
        """Mutating an argument inside a memoized function doesn't throw
        an error (but it's probably not a great idea)."""
        with patch.object(st, "exception") as mock_exception:

            @cache_decorator
            def foo(d):
                d["answer"] += 1
                return d["answer"]

            d = {"answer": 0}

            self.assertEqual(foo(d), 1)
            self.assertEqual(foo(d), 2)

            mock_exception.assert_not_called()