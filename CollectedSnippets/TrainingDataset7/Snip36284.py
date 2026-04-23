def test_microseconds(self):
        duration = datetime.timedelta(hours=1, minutes=3, seconds=5, microseconds=12345)
        self.assertEqual(duration_iso_string(duration), "P0DT01H03M05.012345S")