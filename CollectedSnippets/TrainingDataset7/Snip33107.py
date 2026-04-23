def test_timesince16(self):
        output = self.engine.render_to_string(
            "timesince16", {"a": self.now_tz_i, "b": self.now}
        )
        self.assertEqual(output, "")