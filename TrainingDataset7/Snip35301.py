def test_context_manager_failure(self):
        msg = "Expected message' not found in 'Unexpected message'"
        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertWarnsMessage(UserWarning, "Expected message"):
                warnings.warn("Unexpected message", UserWarning)