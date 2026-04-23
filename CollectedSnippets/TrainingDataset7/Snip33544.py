def test_inheritance13(self):
        """
        Three-level with this level overriding second level
        """
        output = self.engine.render_to_string("inheritance13")
        self.assertEqual(output, "1a3b")