def test_inheritance21(self):
        """
        Three-level inheritance with {{ block.super }} from parent
        """
        output = self.engine.render_to_string("inheritance21")
        self.assertEqual(output, "12a34")