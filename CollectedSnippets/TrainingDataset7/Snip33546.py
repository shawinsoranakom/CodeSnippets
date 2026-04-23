def test_inheritance15(self):
        """
        A block within another block
        """
        output = self.engine.render_to_string("inheritance15")
        self.assertEqual(output, "12inner3_")