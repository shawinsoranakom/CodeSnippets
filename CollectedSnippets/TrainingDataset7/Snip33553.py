def test_inheritance22(self):
        """
        Three-level inheritance with {{ block.super }} from grandparent
        """
        output = self.engine.render_to_string("inheritance22")
        self.assertEqual(output, "1&a3_")