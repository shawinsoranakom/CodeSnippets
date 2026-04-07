def validate_consistency(self):
        """Ensure there are no dummy nodes remaining in the graph."""
        [n.raise_error() for n in self.node_map.values() if isinstance(n, DummyNode)]