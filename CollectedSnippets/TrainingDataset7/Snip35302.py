def test_callable(self):
        def func():
            warnings.warn("Expected message", UserWarning)

        self.assertWarnsMessage(UserWarning, "Expected message", func)