def test_timesince02(self):
        output = self.engine.render_to_string(
            "timesince02", {"a": datetime.now() - timedelta(days=1, minutes=1)}
        )
        self.assertEqual(output, "1\xa0day")