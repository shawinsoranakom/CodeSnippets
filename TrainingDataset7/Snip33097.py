def test_timesince06(self):
        output = self.engine.render_to_string(
            "timesince06", {"a": self.now_tz - timedelta(hours=8), "b": self.now_tz}
        )
        self.assertEqual(output, "8\xa0hours")