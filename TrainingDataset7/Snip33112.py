def test_since_now(self):
        self.assertEqual(timesince_filter(datetime.now() - timedelta(1)), "1\xa0day")