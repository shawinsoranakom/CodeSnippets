def test_timeuntil03(self):
        output = self.engine.render_to_string(
            "timeuntil03",
            {"a": (datetime.now() + timedelta(hours=8, minutes=10, seconds=10))},
        )
        self.assertEqual(output, "8\xa0hours, 10\xa0minutes")