def test_reorder_tests_same_type_consecutive(self):
        """Tests of the same type are made consecutive."""
        tests = self.make_tests()
        # Move the last item to the front.
        tests.insert(0, tests.pop())
        self.assertTestNames(
            tests,
            expected=[
                "Tests2.test2",
                "Tests1.test1",
                "Tests1.test2",
                "Tests2.test1",
            ],
        )
        reordered_tests = reorder_tests(tests, classes=[])
        self.assertTestNames(
            reordered_tests,
            expected=[
                "Tests2.test2",
                "Tests2.test1",
                "Tests1.test1",
                "Tests1.test2",
            ],
        )