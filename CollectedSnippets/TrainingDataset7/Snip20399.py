def test_trunc_func(self):
        start_datetime = datetime.datetime(999, 6, 15, 14, 30, 50, 321)
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10, 50, 123)
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)

        def assertDatetimeKind(kind):
            truncated_start = truncate_to(start_datetime, kind)
            truncated_end = truncate_to(end_datetime, kind)
            queryset = DTModel.objects.annotate(
                truncated=Trunc("start_datetime", kind, output_field=DateTimeField())
            ).order_by("start_datetime")
            self.assertSequenceEqual(
                queryset.values_list("start_datetime", "truncated"),
                [
                    (start_datetime, truncated_start),
                    (end_datetime, truncated_end),
                ],
            )

        def assertDateKind(kind):
            truncated_start = truncate_to(start_datetime.date(), kind)
            truncated_end = truncate_to(end_datetime.date(), kind)
            queryset = DTModel.objects.annotate(
                truncated=Trunc("start_date", kind, output_field=DateField())
            ).order_by("start_datetime")
            self.assertSequenceEqual(
                queryset.values_list("start_datetime", "truncated"),
                [
                    (start_datetime, truncated_start),
                    (end_datetime, truncated_end),
                ],
            )

        def assertTimeKind(kind):
            truncated_start = truncate_to(start_datetime.time(), kind)
            truncated_end = truncate_to(end_datetime.time(), kind)
            queryset = DTModel.objects.annotate(
                truncated=Trunc("start_time", kind, output_field=TimeField())
            ).order_by("start_datetime")
            self.assertSequenceEqual(
                queryset.values_list("start_datetime", "truncated"),
                [
                    (start_datetime, truncated_start),
                    (end_datetime, truncated_end),
                ],
            )

        def assertDatetimeToTimeKind(kind):
            truncated_start = truncate_to(start_datetime.time(), kind)
            truncated_end = truncate_to(end_datetime.time(), kind)
            queryset = DTModel.objects.annotate(
                truncated=Trunc("start_datetime", kind, output_field=TimeField()),
            ).order_by("start_datetime")
            self.assertSequenceEqual(
                queryset.values_list("start_datetime", "truncated"),
                [
                    (start_datetime, truncated_start),
                    (end_datetime, truncated_end),
                ],
            )

        date_truncations = ["year", "quarter", "month", "day"]
        time_truncations = ["hour", "minute", "second"]
        tests = [
            (assertDateKind, date_truncations),
            (assertTimeKind, time_truncations),
            (assertDatetimeKind, [*date_truncations, *time_truncations]),
            (assertDatetimeToTimeKind, time_truncations),
        ]
        for assertion, truncations in tests:
            for truncation in truncations:
                with self.subTest(assertion=assertion.__name__, truncation=truncation):
                    assertion(truncation)

        qs = DTModel.objects.filter(
            start_datetime__date=Trunc(
                "start_datetime", "day", output_field=DateField()
            )
        )
        self.assertEqual(qs.count(), 2)