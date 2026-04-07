def test_is_picklable_with_non_picklable_properties(self):
        """ParallelTestSuite requires that all TestCases are picklable."""
        self.non_picklable = lambda: 0
        self.assertEqual(self, pickle.loads(pickle.dumps(self)))