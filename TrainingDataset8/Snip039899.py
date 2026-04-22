def test_getattr_nonexistent(self, *mocks):
        """Verify that access to missing attribute raises  AttributeError."""
        with self.assertRaises(AttributeError):
            self.secrets.nonexistent_secret

        with self.assertRaises(AttributeError):
            self.secrets.subsection.nonexistent_secret