def test_cleanups_run_after_tearDown(self):
        calls = []

        class SaveCallsDecorator(TestContextDecorator):
            def enable(self):
                calls.append("enable")

            def disable(self):
                calls.append("disable")

        class AddCleanupInSetUp(unittest.TestCase):
            def setUp(self):
                calls.append("setUp")
                self.addCleanup(lambda: calls.append("cleanup"))

        decorator = SaveCallsDecorator()
        decorated_test_class = decorator.__call__(AddCleanupInSetUp)()
        decorated_test_class.setUp()
        decorated_test_class.tearDown()
        decorated_test_class.doCleanups()
        self.assertEqual(calls, ["enable", "setUp", "cleanup", "disable"])