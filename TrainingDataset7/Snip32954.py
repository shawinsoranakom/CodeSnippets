def test_iriencode02(self):
        output = self.engine.render_to_string("iriencode02", {"url": "?test=1&me=2"})
        self.assertEqual(output, "?test=1&me=2")