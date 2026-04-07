def test_phone2numeric01(self):
        output = self.engine.render_to_string(
            "phone2numeric01",
            {"a": "<1-800-call-me>", "b": mark_safe("<1-800-call-me>")},
        )
        self.assertEqual(output, "&lt;1-800-2255-63&gt; <1-800-2255-63>")