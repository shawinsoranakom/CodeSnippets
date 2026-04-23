def test_negative(self):
        duration = datetime.timedelta(days=-1, hours=1, minutes=3, seconds=5)
        self.assertEqual(duration_string(duration), "-1 01:03:05")