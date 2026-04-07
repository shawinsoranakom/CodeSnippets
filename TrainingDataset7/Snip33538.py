def test_inheritance07(self):
        """
        Two-level with one block defined, one block not defined
        """
        output = self.engine.render_to_string("inheritance07")
        self.assertEqual(output, "1&35")