def test_make_aware_no_tz(self):
        self.assertEqual(
            timezone.make_aware(datetime.datetime(2011, 9, 1, 13, 20, 30)),
            datetime.datetime(
                2011, 9, 1, 13, 20, 30, tzinfo=timezone.get_fixed_timezone(-300)
            ),
        )