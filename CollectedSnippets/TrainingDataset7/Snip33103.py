def test_timesince12(self):
        output = self.engine.render_to_string("timesince12", {"a": self.now_tz})
        self.assertEqual(output, "0\xa0minutes")