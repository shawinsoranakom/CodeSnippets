def test_timesince10(self):
        output = self.engine.render_to_string(
            "timesince10", {"now": self.now, "later": self.now + timedelta(days=7)}
        )
        self.assertEqual(output, "0\xa0minutes")