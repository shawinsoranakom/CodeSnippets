def test_slice02(self):
        output = self.engine.render_to_string(
            "slice02", {"a": "a&b", "b": mark_safe("a&b")}
        )
        self.assertEqual(output, "&b &b")