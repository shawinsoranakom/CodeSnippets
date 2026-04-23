def test_overridable_test_suite(self):
        self.assertEqual(DiscoverRunner().test_suite, TestSuite)