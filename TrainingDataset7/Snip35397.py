def test_exception_in_setup(self, mock_disable):
        """An exception is setUp() is reraised after disable() is called."""

        class ExceptionInSetUp(unittest.TestCase):
            def setUp(self):
                raise NotImplementedError("reraised")

        decorator = DoNothingDecorator()
        decorated_test_class = decorator.__call__(ExceptionInSetUp)()
        self.assertFalse(mock_disable.called)
        with self.assertRaisesMessage(NotImplementedError, "reraised"):
            decorated_test_class.setUp()
        decorated_test_class.doCleanups()
        self.assertTrue(mock_disable.called)