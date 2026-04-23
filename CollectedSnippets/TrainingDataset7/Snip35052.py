def test_reorder_test_bin_no_arguments(self):
        tests = self.make_tests()
        reordered_tests = reorder_test_bin(tests)
        self.assertIsInstance(reordered_tests, collections.abc.Iterator)
        self.assertTestNames(
            reordered_tests,
            expected=[
                "Tests1.test1",
                "Tests1.test2",
                "Tests2.test1",
                "Tests2.test2",
            ],
        )