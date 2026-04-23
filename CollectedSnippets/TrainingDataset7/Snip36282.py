def test_simple(self):
        duration = datetime.timedelta(hours=1, minutes=3, seconds=5)
        self.assertEqual(duration_iso_string(duration), "P0DT01H03M05S")