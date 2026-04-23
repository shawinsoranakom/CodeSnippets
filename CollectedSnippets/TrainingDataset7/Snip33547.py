def test_inheritance16(self):
        """
        A block within another block (level 2)
        """
        output = self.engine.render_to_string("inheritance16")
        self.assertEqual(output, "12out3_")