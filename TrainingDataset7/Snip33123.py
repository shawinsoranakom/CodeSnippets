def test_timeuntil09(self):
        output = self.engine.render_to_string(
            "timeuntil09", {"now": self.now, "later": self.now + timedelta(days=7)}
        )
        self.assertEqual(output, "1\xa0week")