def test_e_format_with_named_time_zone(self):
        dt = datetime(1970, 1, 1, tzinfo=UTC)
        self.assertEqual(dateformat.format(dt, "e"), "UTC")