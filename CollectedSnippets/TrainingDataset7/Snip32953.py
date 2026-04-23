def test_iriencode01(self):
        output = self.engine.render_to_string("iriencode01", {"url": "?test=1&me=2"})
        self.assertEqual(output, "?test=1&amp;me=2")