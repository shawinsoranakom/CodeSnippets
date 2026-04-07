def test_timesince17(self):
        output = self.engine.render_to_string(
            "timesince17", {"a": self.today, "b": self.today}
        )
        self.assertEqual(output, "0\xa0minutes")