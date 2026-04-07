def test_timesince05(self):
        output = self.engine.render_to_string(
            "timesince05",
            {
                "a": self.now - timedelta(days=2, minutes=1),
                "b": self.now - timedelta(days=2),
            },
        )
        self.assertEqual(output, "1\xa0minute")