def test_reorder_test_bin_random_and_reverse(self):
        tests = self.make_tests()
        # Choose a seed that shuffles both the classes and methods.
        shuffler = Shuffler(seed=9)
        reordered_tests = reorder_test_bin(tests, shuffler=shuffler, reverse=True)
        self.assertIsInstance(reordered_tests, collections.abc.Iterator)
        self.assertTestNames(
            reordered_tests,
            expected=[
                "Tests1.test1",
                "Tests1.test2",
                "Tests2.test2",
                "Tests2.test1",
            ],
        )