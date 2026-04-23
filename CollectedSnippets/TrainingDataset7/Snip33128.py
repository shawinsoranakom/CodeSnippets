def test_timeuntil14(self):
        output = self.engine.render_to_string(
            "timeuntil14", {"a": self.today, "b": self.today - timedelta(hours=24)}
        )
        self.assertEqual(output, "1\xa0day")