def test_datetime_range_contains(self):
        filter_args = (
            self.timestamps[1],
            self.aware_timestamps[1],
            (self.timestamps[1], self.timestamps[2]),
            (self.aware_timestamps[1], self.aware_timestamps[2]),
            Value(self.dates[0]),
            Func(F("dates"), function="lower", output_field=DateTimeField()),
            F("timestamps_inner"),
        )
        for filter_arg in filter_args:
            with self.subTest(filter_arg=filter_arg):
                self.assertCountEqual(
                    RangesModel.objects.filter(**{"timestamps__contains": filter_arg}),
                    [self.obj, self.aware_obj],
                )