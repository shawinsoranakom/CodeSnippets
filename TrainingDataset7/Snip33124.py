def test_timeuntil10(self):
        output = self.engine.render_to_string("timeuntil10", {"a": self.now_tz})
        self.assertEqual(output, "0\xa0minutes")