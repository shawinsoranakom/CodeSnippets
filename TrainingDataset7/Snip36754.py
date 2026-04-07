def test_negate(self):
        # negated is False by default
        self.assertFalse(self.node1.negated)
        self.node1.negate()
        self.assertTrue(self.node1.negated)
        self.node1.negate()
        self.assertFalse(self.node1.negated)