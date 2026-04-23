def test_trunc_time_func(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10, 50, 123)
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=TruncTime("start_datetime")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, start_datetime.time()),
                (end_datetime, end_datetime.time()),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertEqual(
            DTModel.objects.filter(
                start_datetime__time=TruncTime("start_datetime")
            ).count(),
            2,
        )

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate DateField 'start_date' to TimeField"
        ):
            list(DTModel.objects.annotate(truncated=TruncTime("start_date")))

        with self.assertRaisesMessage(
            ValueError, "Cannot truncate DateField 'start_date' to TimeField"
        ):
            list(
                DTModel.objects.annotate(
                    truncated=TruncTime("start_date", output_field=DateField())
                )
            )