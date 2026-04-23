def test_negative(self):
        duration = -1 * datetime.timedelta(days=1, hours=1, minutes=3, seconds=5)
        self.assertEqual(duration_iso_string(duration), "-P1DT01H03M05S")