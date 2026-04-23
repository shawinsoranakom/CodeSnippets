def test_timesince07(self):
        output = self.engine.render_to_string(
            "timesince07", {"earlier": self.now - timedelta(days=7)}
        )
        self.assertEqual(output, "1\xa0week")