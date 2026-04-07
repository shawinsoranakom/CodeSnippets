def test_message(self):
        msg = (
            "Expected 'http://example.com/?x=1&x=2' to equal "
            "'https://example.com/?x=2&x=1'"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertURLEqual(
                "http://example.com/?x=1&x=2", "https://example.com/?x=2&x=1"
            )