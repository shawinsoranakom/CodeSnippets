def test_wordwrap01(self):
        output = self.engine.render_to_string(
            "wordwrap01", {"a": "a & b", "b": mark_safe("a & b")}
        )
        self.assertEqual(output, "a &\nb a &\nb")