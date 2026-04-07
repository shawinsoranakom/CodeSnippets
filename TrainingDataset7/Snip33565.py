def test_inheritance34(self):
        """
        Inherit from a template with block wrapped in an {% if %} tag
        (in parent), still gets overridden
        """
        output = self.engine.render_to_string("inheritance34", {"optional": 1})
        self.assertEqual(output, "1two3")