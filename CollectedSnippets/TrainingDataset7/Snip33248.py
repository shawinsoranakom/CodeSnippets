def test_wordcount01(self):
        output = self.engine.render_to_string(
            "wordcount01", {"a": "a & b", "b": mark_safe("a &amp; b")}
        )
        self.assertEqual(output, "3 3")