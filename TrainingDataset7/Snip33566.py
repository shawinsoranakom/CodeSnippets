def test_inheritance35(self):
        """
        Inherit from a template with block wrapped in an {% if %} tag
        (in parent), still gets overridden
        """
        output = self.engine.render_to_string("inheritance35", {"optional": 2})
        self.assertEqual(output, "13")