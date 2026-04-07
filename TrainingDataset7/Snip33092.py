def test_timesince01(self):
        output = self.engine.render_to_string(
            "timesince01", {"a": datetime.now() + timedelta(minutes=-1, seconds=-10)}
        )
        self.assertEqual(output, "1\xa0minute")