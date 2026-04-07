def build_test_suite(self, test_classes, suite=None, suite_class=None):
        if suite_class is None:
            suite_class = unittest.TestSuite
        if suite is None:
            suite = suite_class()

        loader = unittest.defaultTestLoader
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            subsuite = suite_class()
            # Only use addTest() to simplify testing a custom TestSuite.
            for test in tests:
                subsuite.addTest(test)
            suite.addTest(subsuite)

        return suite