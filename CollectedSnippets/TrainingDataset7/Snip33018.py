def test_lower01(self):
        output = self.engine.render_to_string(
            "lower01", {"a": "Apple & banana", "b": mark_safe("Apple &amp; banana")}
        )
        self.assertEqual(output, "apple & banana apple &amp; banana")