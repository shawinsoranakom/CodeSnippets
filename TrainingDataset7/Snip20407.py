def test_trunc_month_func(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = truncate_to(
            datetime.datetime(2016, 6, 15, 14, 10, 50, 123), "month"
        )
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncMonth("start_datetime")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, truncate_to(start_datetime, "month")),
                (end_datetime, truncate_to(end_datetime, "month")),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncMonth("start_date")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, truncate_to(start_datetime.date(), "month")),
                (end_datetime, truncate_to(end_datetime.date(), "month")),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertEqual(
            DTModel.objects.filter(start_datetime=TruncMonth("start_datetime")).count(),
            1,
        )

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate TimeField 'start_time' to DateTimeField"
        ):
            list(DTModel.objects.annotate(truncated=TruncMonth("start_time")))

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate TimeField 'start_time' to DateTimeField"
        ):
            list(
                DTModel.objects.annotate(
                    truncated=TruncMonth("start_time", output_field=TimeField())
                )
            )