def test_inheritance01(self):
        """
        Standard template with no inheritance
        """
        output = self.engine.render_to_string("inheritance01")
        self.assertEqual(output, "1&3_")