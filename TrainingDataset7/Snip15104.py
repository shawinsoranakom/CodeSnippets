def test_bounded_params_with_dst_time_zone(self):
        tests = [
            # Northern hemisphere.
            ("Asia/Jerusalem", 3),
            ("Asia/Jerusalem", 10),
            # Southern hemisphere.
            ("Pacific/Chatham", 4),
            ("Pacific/Chatham", 9),
        ]
        for time_zone, month in tests:
            with self.subTest(time_zone=time_zone, month=month):
                with self.settings(USE_TZ=True, TIME_ZONE=time_zone):
                    self.assertDateParams(
                        {"year": 2019, "month": month},
                        make_aware(datetime(2019, month, 1)),
                        make_aware(datetime(2019, month + 1, 1)),
                    )