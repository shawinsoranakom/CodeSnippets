def test_lower02(self):
        output = self.engine.render_to_string(
            "lower02", {"a": "Apple & banana", "b": mark_safe("Apple &amp; banana")}
        )
        self.assertEqual(output, "apple &amp; banana apple &amp; banana")