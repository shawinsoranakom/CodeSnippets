def test_setupclass_override(self):
        """Settings are overridden within setUpClass (#21281)."""
        self.assertEqual(self.foo, "override")