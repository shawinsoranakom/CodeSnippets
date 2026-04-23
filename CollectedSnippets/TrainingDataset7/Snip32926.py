def test_floatformat01(self):
        output = self.engine.render_to_string(
            "floatformat01", {"a": "1.42", "b": mark_safe("1.42")}
        )
        self.assertEqual(output, "1.4 1.4")