def test_inheritance11(self):
        """
        Three-level with both blocks defined on this level, but none on
        second level
        """
        output = self.engine.render_to_string("inheritance11")
        self.assertEqual(output, "1234")