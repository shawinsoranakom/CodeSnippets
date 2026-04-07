def test_microseconds(self):
        duration = datetime.timedelta(hours=1, minutes=3, seconds=5, microseconds=12345)
        self.assertEqual(duration_string(duration), "01:03:05.012345")