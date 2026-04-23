def test_simple(self):
        duration = datetime.timedelta(hours=1, minutes=3, seconds=5)
        self.assertEqual(duration_string(duration), "01:03:05")