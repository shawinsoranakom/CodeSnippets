def test_inheritance30(self):
        """
        Base template, putting block in a conditional {% if %} tag
        """
        output = self.engine.render_to_string("inheritance30", {"optional": True})
        self.assertEqual(output, "123")