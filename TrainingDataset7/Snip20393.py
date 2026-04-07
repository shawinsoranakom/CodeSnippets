def test_extract_iso_weekday_func(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10, 50, 123)
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=ExtractIsoWeekDay("start_datetime"),
            ).order_by("start_datetime"),
            [
                (start_datetime, start_datetime.isoweekday()),
                (end_datetime, end_datetime.isoweekday()),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=ExtractIsoWeekDay("start_date"),
            ).order_by("start_datetime"),
            [
                (start_datetime, start_datetime.isoweekday()),
                (end_datetime, end_datetime.isoweekday()),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertEqual(
            DTModel.objects.filter(
                start_datetime__week_day=ExtractWeekDay("start_datetime"),
            ).count(),
            2,
        )