def test_timeuntil13(self):
        output = self.engine.render_to_string(
            "timeuntil13", {"a": self.today, "b": self.today}
        )
        self.assertEqual(output, "0\xa0minutes")