def test_timeuntil06(self):
        output = self.engine.render_to_string(
            "timeuntil06", {"earlier": self.now - timedelta(days=7)}
        )
        self.assertEqual(output, "0\xa0minutes")