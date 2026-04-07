def test_slice01(self):
        output = self.engine.render_to_string(
            "slice01", {"a": "a&b", "b": mark_safe("a&b")}
        )
        self.assertEqual(output, "&amp;b &b")