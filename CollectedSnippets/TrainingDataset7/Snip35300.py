def test_context_manager(self):
        with self.assertWarnsMessage(UserWarning, "Expected message"):
            warnings.warn("Expected message", UserWarning)