def test_extract_duration(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10, 50, 123)
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)
        self.assertQuerySetEqual(
            DTModel.objects.annotate(extracted=Extract("duration", "second")).order_by(
                "start_datetime"
            ),
            [
                (start_datetime, (end_datetime - start_datetime).seconds % 60),
                (end_datetime, (start_datetime - end_datetime).seconds % 60),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertEqual(
            DTModel.objects.annotate(
                duration_days=Extract("duration", "day"),
            )
            .filter(duration_days__gt=200)
            .count(),
            1,
        )