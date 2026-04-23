def test_timeuntil07(self):
        output = self.engine.render_to_string(
            "timeuntil07", {"now": self.now, "earlier": self.now - timedelta(days=7)}
        )
        self.assertEqual(output, "0\xa0minutes")