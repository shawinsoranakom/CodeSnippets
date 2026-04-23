def test_extract_week_func_boundaries(self):
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10, 50, 123)
        if settings.USE_TZ:
            end_datetime = timezone.make_aware(end_datetime)

        week_52_day_2014 = datetime.datetime(2014, 12, 27, 13, 0)  # Sunday
        week_1_day_2014_2015 = datetime.datetime(2014, 12, 31, 13, 0)  # Wednesday
        week_53_day_2015 = datetime.datetime(2015, 12, 31, 13, 0)  # Thursday
        if settings.USE_TZ:
            week_1_day_2014_2015 = timezone.make_aware(week_1_day_2014_2015)
            week_52_day_2014 = timezone.make_aware(week_52_day_2014)
            week_53_day_2015 = timezone.make_aware(week_53_day_2015)

        days = [week_52_day_2014, week_1_day_2014_2015, week_53_day_2015]
        self.create_model(week_53_day_2015, end_datetime)
        self.create_model(week_52_day_2014, end_datetime)
        self.create_model(week_1_day_2014_2015, end_datetime)
        qs = (
            DTModel.objects.filter(start_datetime__in=days)
            .annotate(
                extracted=ExtractWeek("start_datetime"),
            )
            .order_by("start_datetime")
        )
        self.assertQuerySetEqual(
            qs,
            [
                (week_52_day_2014, 52),
                (week_1_day_2014_2015, 1),
                (week_53_day_2015, 53),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )