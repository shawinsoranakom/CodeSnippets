def test_trunc_year_func(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = truncate_to(
            datetime.datetime(2016, 6, 15, 14, 10, 50, 123), "year"
        )
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncYear("start_datetime")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, truncate_to(start_datetime, "year")),
                (end_datetime, truncate_to(end_datetime, "year")),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncYear("start_date")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, truncate_to(start_datetime.date(), "year")),
                (end_datetime, truncate_to(end_datetime.date(), "year")),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertEqual(
            DTModel.objects.filter(start_datetime=TruncYear("start_datetime")).count(),
            1,
        )

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate TimeField 'start_time' to DateTimeField"
        ):
            list(DTModel.objects.annotate(truncated=TruncYear("start_time")))

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate TimeField 'start_time' to DateTimeField"
        ):
            list(
                DTModel.objects.annotate(
                    truncated=TruncYear("start_time", output_field=TimeField())
                )
            )