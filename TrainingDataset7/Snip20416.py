def test_trunc_minute_func(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = truncate_to(
            datetime.datetime(2016, 6, 15, 14, 10, 50, 123), "minute"
        )
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncMinute("start_datetime")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, truncate_to(start_datetime, "minute")),
                (end_datetime, truncate_to(end_datetime, "minute")),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncMinute("start_time")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, truncate_to(start_datetime.time(), "minute")),
                (end_datetime, truncate_to(end_datetime.time(), "minute")),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertEqual(
            DTModel.objects.filter(
                start_datetime=TruncMinute("start_datetime")
            ).count(),
            1,
        )

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate DateField 'start_date' to DateTimeField"
        ):
            list(DTModel.objects.annotate(truncated=TruncMinute("start_date")))

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate DateField 'start_date' to DateTimeField"
        ):
            list(
                DTModel.objects.annotate(
                    truncated=TruncMinute("start_date", output_field=DateField())
                )
            )