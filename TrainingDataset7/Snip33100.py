def test_timesince09(self):
        output = self.engine.render_to_string(
            "timesince09", {"later": self.now + timedelta(days=7)}
        )
        self.assertEqual(output, "0\xa0minutes")