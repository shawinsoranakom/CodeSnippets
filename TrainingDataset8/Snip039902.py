def test_getitem_nonexistent(self, *mocks):
        """Verify that access to missing key via dict notation raises KeyError."""
        with self.assertRaises(KeyError):
            self.secrets["nonexistent_secret"]

        with self.assertRaises(KeyError):
            self.secrets["subsection"]["nonexistent_secret"]