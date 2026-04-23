def test_inheritance37(self):
        """
        Inherit from a template with block wrapped in an {% for %} tag
        (in parent), still gets overridden
        """
        output = self.engine.render_to_string("inheritance37", {"numbers": "123"})
        self.assertEqual(output, "_X_X_X_")