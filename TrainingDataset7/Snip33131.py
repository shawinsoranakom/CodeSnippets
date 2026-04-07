def test_until_now(self):
        self.assertEqual(timeuntil_filter(datetime.now() + timedelta(1, 1)), "1\xa0day")