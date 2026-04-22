def test_memoization(self):
        """Test that util.memoize works."""
        non_memoized_func = lambda: random.randint(0, 1000000)
        yes_memoized_func = util.memoize(non_memoized_func)
        self.assertNotEqual(non_memoized_func(), non_memoized_func())
        self.assertEqual(yes_memoized_func(), yes_memoized_func())