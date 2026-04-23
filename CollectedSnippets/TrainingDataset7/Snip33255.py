def test_wordwrap02(self):
        output = self.engine.render_to_string(
            "wordwrap02", {"a": "a & b", "b": mark_safe("a & b")}
        )
        self.assertEqual(output, "a &amp;\nb a &\nb")