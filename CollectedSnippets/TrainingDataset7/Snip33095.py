def test_timesince04(self):
        output = self.engine.render_to_string(
            "timesince04",
            {"a": self.now - timedelta(days=2), "b": self.now - timedelta(days=1)},
        )
        self.assertEqual(output, "1\xa0day")