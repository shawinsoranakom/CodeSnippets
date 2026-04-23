def test_date_range_contains(self):
        filter_args = (
            self.timestamps[1],
            (self.dates[1], self.dates[2]),
            Value(self.dates[0], output_field=DateField()),
            Func(F("timestamps"), function="lower", output_field=DateField()),
            F("dates_inner"),
        )
        for filter_arg in filter_args:
            with self.subTest(filter_arg=filter_arg):
                self.assertCountEqual(
                    RangesModel.objects.filter(**{"dates__contains": filter_arg}),
                    [self.obj, self.aware_obj],
                )