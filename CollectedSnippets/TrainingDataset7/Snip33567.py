def test_inheritance36(self):
        """
        Base template, putting block in a {% for %} tag
        """
        output = self.engine.render_to_string("inheritance36", {"numbers": "123"})
        self.assertEqual(output, "_1_2_3_")