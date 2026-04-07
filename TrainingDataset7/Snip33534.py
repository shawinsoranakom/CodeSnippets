def test_inheritance03(self):
        """
        Three-level with no redefinitions on third level
        """
        output = self.engine.render_to_string("inheritance03")
        self.assertEqual(output, "1234")