def test_wordcount02(self):
        output = self.engine.render_to_string(
            "wordcount02", {"a": "a & b", "b": mark_safe("a &amp; b")}
        )
        self.assertEqual(output, "3 3")