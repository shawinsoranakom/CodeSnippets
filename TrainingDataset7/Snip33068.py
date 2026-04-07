def test_slugify02(self):
        output = self.engine.render_to_string(
            "slugify02", {"a": "a & b", "b": mark_safe("a &amp; b")}
        )
        self.assertEqual(output, "a-b a-amp-b")