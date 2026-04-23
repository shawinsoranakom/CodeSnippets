def test_trunc_func_with_timezone(self):
        """
        If the truncated datetime transitions to a different offset (daylight
        saving) then the returned value will have that new timezone/offset.
        """
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10, 50, 123)
        start_datetime = timezone.make_aware(start_datetime)
        end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)

        def assertDatetimeKind(kind, tzinfo):
            truncated_start = truncate_to(
                start_datetime.astimezone(tzinfo), kind, tzinfo
            )
            truncated_end = truncate_to(end_datetime.astimezone(tzinfo), kind, tzinfo)
            queryset = DTModel.objects.annotate(
                truncated=Trunc(
                    "start_datetime",
                    kind,
                    output_field=DateTimeField(),
                    tzinfo=tzinfo,
                )
            ).order_by("start_datetime")
            self.assertSequenceEqual(
                queryset.values_list("start_datetime", "truncated"),
                [
                    (start_datetime, truncated_start),
                    (end_datetime, truncated_end),
                ],
            )

        def assertDatetimeToDateKind(kind, tzinfo):
            truncated_start = truncate_to(
                start_datetime.astimezone(tzinfo).date(), kind
            )
            truncated_end = truncate_to(end_datetime.astimezone(tzinfo).date(), kind)
            queryset = DTModel.objects.annotate(
                truncated=Trunc(
                    "start_datetime",
                    kind,
                    output_field=DateField(),
                    tzinfo=tzinfo,
                ),
            ).order_by("start_datetime")
            self.assertSequenceEqual(
                queryset.values_list("start_datetime", "truncated"),
                [
                    (start_datetime, truncated_start),
                    (end_datetime, truncated_end),
                ],
            )

        def assertDatetimeToTimeKind(kind, tzinfo):
            truncated_start = truncate_to(
                start_datetime.astimezone(tzinfo).time(), kind
            )
            truncated_end = truncate_to(end_datetime.astimezone(tzinfo).time(), kind)
            queryset = DTModel.objects.annotate(
                truncated=Trunc(
                    "start_datetime",
                    kind,
                    output_field=TimeField(),
                    tzinfo=tzinfo,
                )
            ).order_by("start_datetime")
            self.assertSequenceEqual(
                queryset.values_list("start_datetime", "truncated"),
                [
                    (start_datetime, truncated_start),
                    (end_datetime, truncated_end),
                ],
            )

        timezones = [
            zoneinfo.ZoneInfo("Australia/Melbourne"),
            zoneinfo.ZoneInfo("Etc/GMT+10"),
        ]
        date_truncations = ["year", "quarter", "month", "week", "day"]
        time_truncations = ["hour", "minute", "second"]
        tests = [
            (assertDatetimeToDateKind, date_truncations),
            (assertDatetimeToTimeKind, time_truncations),
            (assertDatetimeKind, [*date_truncations, *time_truncations]),
        ]
        for assertion, truncations in tests:
            for truncation in truncations:
                for tzinfo in timezones:
                    with self.subTest(
                        assertion=assertion.__name__,
                        truncation=truncation,
                        tzinfo=tzinfo.key,
                    ):
                        assertion(truncation, tzinfo)

        qs = DTModel.objects.filter(
            start_datetime__date=Trunc(
                "start_datetime", "day", output_field=DateField()
            )
        )
        self.assertEqual(qs.count(), 2)