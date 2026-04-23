def test_inheritance38(self):
        """
        Inherit from a template with block wrapped in an {% for %} tag
        (in parent), still gets overridden
        """
        output = self.engine.render_to_string("inheritance38")
        self.assertEqual(output, "_")