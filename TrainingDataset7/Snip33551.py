def test_inheritance20(self):
        """
        Two-level inheritance with {{ block.super }}
        """
        output = self.engine.render_to_string("inheritance20")
        self.assertEqual(output, "1&a3_")