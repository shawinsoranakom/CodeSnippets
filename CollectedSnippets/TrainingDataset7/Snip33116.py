def test_timeuntil02(self):
        output = self.engine.render_to_string(
            "timeuntil02", {"a": (datetime.now() + timedelta(days=1, seconds=10))}
        )
        self.assertEqual(output, "1\xa0day")