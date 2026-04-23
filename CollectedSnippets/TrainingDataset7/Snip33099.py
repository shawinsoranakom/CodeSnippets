def test_timesince08(self):
        output = self.engine.render_to_string(
            "timesince08", {"now": self.now, "earlier": self.now - timedelta(days=7)}
        )
        self.assertEqual(output, "1\xa0week")