def test_iriencode04(self):
        output = self.engine.render_to_string(
            "iriencode04", {"url": mark_safe("?test=1&me=2")}
        )
        self.assertEqual(output, "?test=1&me=2")