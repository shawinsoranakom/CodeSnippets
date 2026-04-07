def test_trunc_week(self):
        self._test_trunc_week(
            start_datetime=datetime.datetime(2015, 6, 15, 14, 30, 50, 321),
            end_datetime=datetime.datetime(2016, 6, 15, 14, 10, 50, 123),
        )