def test_inheritance09(self):
        """
        Three-level with second and third levels blank
        """
        output = self.engine.render_to_string("inheritance09")
        self.assertEqual(output, "1&3_")