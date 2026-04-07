def test_iriencode03(self):
        output = self.engine.render_to_string(
            "iriencode03", {"url": mark_safe("?test=1&me=2")}
        )
        self.assertEqual(output, "?test=1&me=2")