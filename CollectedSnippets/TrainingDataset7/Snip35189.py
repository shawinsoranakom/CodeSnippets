def test_identity_preservation(self):
        """Identity of test data is preserved between accesses."""
        self.assertIs(self.jim_douglas, self.jim_douglas)