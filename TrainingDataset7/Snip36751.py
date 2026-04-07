def test_contains(self):
        self.assertIn(("a", 1), self.node1)
        self.assertNotIn(("a", 1), self.node2)