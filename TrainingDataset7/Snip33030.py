def test_phone2numeric02(self):
        output = self.engine.render_to_string(
            "phone2numeric02",
            {"a": "<1-800-call-me>", "b": mark_safe("<1-800-call-me>")},
        )
        self.assertEqual(output, "<1-800-2255-63> <1-800-2255-63>")