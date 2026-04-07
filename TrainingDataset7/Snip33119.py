def test_timeuntil05(self):
        output = self.engine.render_to_string(
            "timeuntil05",
            {
                "a": self.now - timedelta(days=2),
                "b": self.now - timedelta(days=2, minutes=1),
            },
        )
        self.assertEqual(output, "1\xa0minute")