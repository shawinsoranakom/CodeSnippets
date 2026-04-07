def test_inheritance33(self):
        """
        Base template, putting block in a conditional {% if %} tag
        """
        output = self.engine.render_to_string("inheritance33", {"optional": 1})
        self.assertEqual(output, "123")