def test_timeuntil04(self):
        output = self.engine.render_to_string(
            "timeuntil04",
            {"a": self.now - timedelta(days=1), "b": self.now - timedelta(days=2)},
        )
        self.assertEqual(output, "1\xa0day")