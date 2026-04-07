def test_reorder_tests_reverse_with_duplicates(self):
        class Tests1(unittest.TestCase):
            def test1(self):
                pass

        class Tests2(unittest.TestCase):
            def test2(self):
                pass

            def test3(self):
                pass

        suite = self.build_test_suite((Tests1, Tests2))
        subsuite = list(suite)[0]
        suite.addTest(subsuite)
        tests = list(iter_test_cases(suite))
        self.assertTestNames(
            tests,
            expected=[
                "Tests1.test1",
                "Tests2.test2",
                "Tests2.test3",
                "Tests1.test1",
            ],
        )
        reordered_tests = reorder_tests(tests, classes=[])
        self.assertTestNames(
            reordered_tests,
            expected=[
                "Tests1.test1",
                "Tests2.test2",
                "Tests2.test3",
            ],
        )
        reordered_tests = reorder_tests(tests, classes=[], reverse=True)
        self.assertTestNames(
            reordered_tests,
            expected=[
                "Tests2.test3",
                "Tests2.test2",
                "Tests1.test1",
            ],
        )