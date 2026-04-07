def test_class_decorator(self):
        # SimpleTestCase can be decorated by override_settings, but not
        # ut.TestCase
        class SimpleTestCaseSubclass(SimpleTestCase):
            pass

        class UnittestTestCaseSubclass(unittest.TestCase):
            pass

        decorated = override_settings(TEST="override")(SimpleTestCaseSubclass)
        self.assertIsInstance(decorated, type)
        self.assertTrue(issubclass(decorated, SimpleTestCase))

        with self.assertRaisesMessage(
            Exception, "Only subclasses of Django SimpleTestCase"
        ):
            decorated = override_settings(TEST="override")(UnittestTestCaseSubclass)