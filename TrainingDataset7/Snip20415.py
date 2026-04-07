def test_trunc_hour_func(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = truncate_to(
            datetime.datetime(2016, 6, 15, 14, 10, 50, 123), "hour"
        )
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncHour("start_datetime")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, truncate_to(start_datetime, "hour")),
                (end_datetime, truncate_to(end_datetime, "hour")),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncHour("start_time")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, truncate_to(start_datetime.time(), "hour")),
                (end_datetime, truncate_to(end_datetime.time(), "hour")),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertEqual(
            DTModel.objects.filter(start_datetime=TruncHour("start_datetime")).count(),
            1,
        )

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate DateField 'start_date' to DateTimeField"
        ):
            list(DTModel.objects.annotate(truncated=TruncHour("start_date")))

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate DateField 'start_date' to DateTimeField"
        ):
            list(
                DTModel.objects.annotate(
                    truncated=TruncHour("start_date", output_field=DateField())
                )
            )