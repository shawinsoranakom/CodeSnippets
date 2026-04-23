def test_microsecond(self):
        # Regression test for #18951
        dt = datetime(2009, 5, 16, microsecond=123)
        self.assertEqual(dateformat.format(dt, "u"), "000123")