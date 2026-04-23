def test_exists(self):
        """Runtime.exists() returns True iff the Runtime singleton exists."""
        self.assertFalse(Runtime.exists())
        _ = Runtime(MagicMock())
        self.assertTrue(Runtime.exists())