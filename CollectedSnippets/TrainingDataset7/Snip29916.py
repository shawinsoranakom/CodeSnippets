def setUpTestData(cls):
        cls.timestamps = [
            datetime.datetime(year=2016, month=1, day=1),
            datetime.datetime(year=2016, month=1, day=2, hour=1),
            datetime.datetime(year=2016, month=1, day=2, hour=12),
            datetime.datetime(year=2016, month=1, day=3),
            datetime.datetime(year=2016, month=1, day=3, hour=1),
            datetime.datetime(year=2016, month=2, day=2),
        ]
        cls.aware_timestamps = [
            timezone.make_aware(timestamp) for timestamp in cls.timestamps
        ]
        cls.dates = [
            datetime.date(year=2016, month=1, day=1),
            datetime.date(year=2016, month=1, day=2),
            datetime.date(year=2016, month=1, day=3),
            datetime.date(year=2016, month=1, day=4),
            datetime.date(year=2016, month=2, day=2),
            datetime.date(year=2016, month=2, day=3),
        ]
        cls.obj = RangesModel.objects.create(
            dates=(cls.dates[0], cls.dates[3]),
            dates_inner=(cls.dates[1], cls.dates[2]),
            timestamps=(cls.timestamps[0], cls.timestamps[3]),
            timestamps_inner=(cls.timestamps[1], cls.timestamps[2]),
        )
        cls.aware_obj = RangesModel.objects.create(
            dates=(cls.dates[0], cls.dates[3]),
            dates_inner=(cls.dates[1], cls.dates[2]),
            timestamps=(cls.aware_timestamps[0], cls.aware_timestamps[3]),
            timestamps_inner=(cls.timestamps[1], cls.timestamps[2]),
        )
        # Objects that don't match any queries.
        for i in range(3, 4):
            RangesModel.objects.create(
                dates=(cls.dates[i], cls.dates[i + 1]),
                timestamps=(cls.timestamps[i], cls.timestamps[i + 1]),
            )
            RangesModel.objects.create(
                dates=(cls.dates[i], cls.dates[i + 1]),
                timestamps=(cls.aware_timestamps[i], cls.aware_timestamps[i + 1]),
            )