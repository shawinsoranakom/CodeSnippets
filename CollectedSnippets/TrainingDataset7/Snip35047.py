def test_iter_test_cases_iterable_of_tests(self):
        class Tests(unittest.TestCase):
            def test1(self):
                pass

            def test2(self):
                pass

        tests = list(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        actual_tests = iter_test_cases(tests)
        self.assertTestNames(
            actual_tests,
            expected=[
                "Tests.test1",
                "Tests.test2",
            ],
        )