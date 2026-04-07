def test_upper02(self):
        output = self.engine.render_to_string(
            "upper02", {"a": "a & b", "b": mark_safe("a &amp; b")}
        )
        self.assertEqual(output, "A &amp; B A &amp;AMP; B")