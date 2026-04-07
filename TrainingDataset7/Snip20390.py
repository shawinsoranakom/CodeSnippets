def test_extract_quarter_func_boundaries(self):
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10, 50, 123)
        if settings.USE_TZ:
            end_datetime = timezone.make_aware(end_datetime)

        last_quarter_2014 = datetime.datetime(2014, 12, 31, 13, 0)
        first_quarter_2015 = datetime.datetime(2015, 1, 1, 13, 0)
        if settings.USE_TZ:
            last_quarter_2014 = timezone.make_aware(last_quarter_2014)
            first_quarter_2015 = timezone.make_aware(first_quarter_2015)
        dates = [last_quarter_2014, first_quarter_2015]
        self.create_model(last_quarter_2014, end_datetime)
        self.create_model(first_quarter_2015, end_datetime)
        qs = (
            DTModel.objects.filter(start_datetime__in=dates)
            .annotate(
                extracted=ExtractQuarter("start_datetime"),
            )
            .order_by("start_datetime")
        )
        self.assertQuerySetEqual(
            qs,
            [
                (last_quarter_2014, 4),
                (first_quarter_2015, 1),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )