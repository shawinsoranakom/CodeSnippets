def test_slugify01(self):
        output = self.engine.render_to_string(
            "slugify01", {"a": "a & b", "b": mark_safe("a &amp; b")}
        )
        self.assertEqual(output, "a-b a-amp-b")