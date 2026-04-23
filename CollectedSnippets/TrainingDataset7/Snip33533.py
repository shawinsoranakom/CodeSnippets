def test_inheritance02(self):
        """
        Standard two-level inheritance
        """
        output = self.engine.render_to_string("inheritance02")
        self.assertEqual(output, "1234")