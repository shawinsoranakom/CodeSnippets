def test_timeuntil08(self):
        output = self.engine.render_to_string(
            "timeuntil08", {"later": self.now + timedelta(days=7, hours=1)}
        )
        self.assertEqual(output, "1\xa0week")