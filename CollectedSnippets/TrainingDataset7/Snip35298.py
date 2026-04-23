def test_assert_raises_message(self):
        msg = "'Expected message' not found in 'Unexpected message'"
        # context manager form of assertRaisesMessage()
        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertRaisesMessage(ValueError, "Expected message"):
                raise ValueError("Unexpected message")

        # callable form
        def func():
            raise ValueError("Unexpected message")

        with self.assertRaisesMessage(AssertionError, msg):
            self.assertRaisesMessage(ValueError, "Expected message", func)