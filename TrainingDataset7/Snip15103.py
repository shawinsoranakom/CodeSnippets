def test_bounded_params_with_time_zone(self):
        with self.settings(USE_TZ=True, TIME_ZONE="Asia/Jerusalem"):
            self.assertDateParams(
                {"year": 2017, "month": 2, "day": 28},
                make_aware(datetime(2017, 2, 28)),
                make_aware(datetime(2017, 3, 1)),
            )