def test_eq_negated(self):
        node = Node(negated=False)
        negated = Node(negated=True)
        self.assertNotEqual(negated, node)