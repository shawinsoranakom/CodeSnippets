def test_trunc_quarter_func(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = truncate_to(
            datetime.datetime(2016, 10, 15, 14, 10, 50, 123), "quarter"
        )
        last_quarter_2015 = truncate_to(
            datetime.datetime(2015, 12, 31, 14, 10, 50, 123), "quarter"
        )
        first_quarter_2016 = truncate_to(
            datetime.datetime(2016, 1, 1, 14, 10, 50, 123), "quarter"
        )
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
            last_quarter_2015 = timezone.make_aware(last_quarter_2015)
            first_quarter_2016 = timezone.make_aware(first_quarter_2016)
        self.create_model(start_datetime=start_datetime, end_datetime=end_datetime)
        self.create_model(start_datetime=end_datetime, end_datetime=start_datetime)
        self.create_model(start_datetime=last_quarter_2015, end_datetime=end_datetime)
        self.create_model(start_datetime=first_quarter_2016, end_datetime=end_datetime)
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncQuarter("start_date")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, truncate_to(start_datetime.date(), "quarter")),
                (last_quarter_2015, truncate_to(last_quarter_2015.date(), "quarter")),
                (first_quarter_2016, truncate_to(first_quarter_2016.date(), "quarter")),
                (end_datetime, truncate_to(end_datetime.date(), "quarter")),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncQuarter("start_datetime")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, truncate_to(start_datetime, "quarter")),
                (last_quarter_2015, truncate_to(last_quarter_2015, "quarter")),
                (first_quarter_2016, truncate_to(first_quarter_2016, "quarter")),
                (end_datetime, truncate_to(end_datetime, "quarter")),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate TimeField 'start_time' to DateTimeField"
        ):
            list(DTModel.objects.annotate(truncated=TruncQuarter("start_time")))

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate TimeField 'start_time' to DateTimeField"
        ):
            list(
                DTModel.objects.annotate(
                    truncated=TruncQuarter("start_time", output_field=TimeField())
                )
            )