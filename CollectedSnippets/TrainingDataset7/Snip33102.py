def test_timesince11(self):
        output = self.engine.render_to_string("timesince11", {"a": self.now})
        self.assertEqual(output, "0\xa0minutes")