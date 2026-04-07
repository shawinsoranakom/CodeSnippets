def test_inheritance10(self):
        """
        Three-level with space NOT in a block -- should be ignored
        """
        output = self.engine.render_to_string("inheritance10")
        self.assertEqual(output, "1&3_")