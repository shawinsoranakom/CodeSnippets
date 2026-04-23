def test_timeuntil12(self):
        output = self.engine.render_to_string(
            "timeuntil12", {"a": self.now_tz_i, "b": self.now_tz}
        )
        self.assertEqual(output, "0\xa0minutes")