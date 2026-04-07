def test_inheritance23(self):
        """
        Three-level inheritance with {{ block.super }} from parent and
        grandparent
        """
        output = self.engine.render_to_string("inheritance23")
        self.assertEqual(output, "1&ab3_")