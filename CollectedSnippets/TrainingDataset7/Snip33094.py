def test_timesince03(self):
        output = self.engine.render_to_string(
            "timesince03",
            {"a": datetime.now() - timedelta(hours=1, minutes=25, seconds=10)},
        )
        self.assertEqual(output, "1\xa0hour, 25\xa0minutes")