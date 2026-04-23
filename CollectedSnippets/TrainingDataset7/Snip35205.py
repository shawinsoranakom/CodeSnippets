def test_skip_class_unless_db_feature(self):
        @skipUnlessDBFeature("__class__")
        class NotSkippedTests(TestCase):
            def test_dummy(self):
                return

        @skipUnlessDBFeature("missing")
        @skipIfDBFeature("__class__")
        class SkippedTests(TestCase):
            def test_will_be_skipped(self):
                self.fail("We should never arrive here.")

        @skipIfDBFeature("__dict__")
        class SkippedTestsSubclass(SkippedTests):
            pass

        test_suite = unittest.TestSuite()
        test_suite.addTest(NotSkippedTests("test_dummy"))
        try:
            test_suite.addTest(SkippedTests("test_will_be_skipped"))
            test_suite.addTest(SkippedTestsSubclass("test_will_be_skipped"))
        except unittest.SkipTest:
            self.fail("SkipTest should not be raised here.")
        result = unittest.TextTestRunner(stream=StringIO()).run(test_suite)
        # PY312: Python 3.12.1 does not include skipped tests in the number of
        # running tests.
        self.assertEqual(
            result.testsRun, 1 if sys.version_info[:3] == (3, 12, 1) else 3
        )
        self.assertEqual(len(result.skipped), 2)
        self.assertEqual(result.skipped[0][1], "Database has feature(s) __class__")
        self.assertEqual(result.skipped[1][1], "Database has feature(s) __class__")