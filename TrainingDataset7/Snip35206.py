def test_missing_default_databases(self):
        @skipIfDBFeature("missing")
        class MissingDatabases(SimpleTestCase):
            def test_assertion_error(self):
                pass

        suite = unittest.TestSuite()
        try:
            suite.addTest(MissingDatabases("test_assertion_error"))
        except unittest.SkipTest:
            self.fail("SkipTest should not be raised at this stage")
        runner = unittest.TextTestRunner(stream=StringIO())
        msg = (
            "skipIfDBFeature cannot be used on <class 'test_utils.tests."
            "SkippingClassTestCase.test_missing_default_databases.<locals>."
            "MissingDatabases'> as it doesn't allow queries against the "
            "'default' database."
        )
        with self.assertRaisesMessage(ValueError, msg):
            runner.run(suite)