def test_timeuntil01(self):
        output = self.engine.render_to_string(
            "timeuntil01", {"a": datetime.now() + timedelta(minutes=2, seconds=10)}
        )
        self.assertEqual(output, "2\xa0minutes")