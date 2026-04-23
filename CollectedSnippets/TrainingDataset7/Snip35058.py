def test_reorder_tests_random_mixed_classes(self):
        tests = self.make_tests()
        # Move the last item to the front.
        tests.insert(0, tests.pop())
        shuffler = Shuffler(seed=9)
        self.assertTestNames(
            tests,
            expected=[
                "Tests2.test2",
                "Tests1.test1",
                "Tests1.test2",
                "Tests2.test1",
            ],
        )
        reordered_tests = reorder_tests(tests, classes=[], shuffler=shuffler)
        self.assertTestNames(
            reordered_tests,
            expected=[
                "Tests2.test1",
                "Tests2.test2",
                "Tests1.test2",
                "Tests1.test1",
            ],
        )