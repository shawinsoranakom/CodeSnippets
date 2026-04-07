def test_time_subtraction(self):
        Time.objects.create(time=datetime.time(12, 30, 15, 2345))
        queryset = Time.objects.annotate(
            difference=F("time") - Value(datetime.time(11, 15, 0)),
        )
        self.assertEqual(
            queryset.get().difference,
            datetime.timedelta(hours=1, minutes=15, seconds=15, microseconds=2345),
        )

        queryset = Time.objects.annotate(
            difference=F("time") - Value(None, output_field=TimeField()),
        )
        self.assertIsNone(queryset.first().difference)

        queryset = Time.objects.annotate(
            shifted=ExpressionWrapper(
                F("time") - Value(None, output_field=DurationField()),
                output_field=TimeField(),
            )
        )
        self.assertIsNone(queryset.first().shifted)