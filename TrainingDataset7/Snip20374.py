def test_extract_year_greaterthan_lookup(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 10)
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10)
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)

        for lookup in ("year", "iso_year"):
            with self.subTest(lookup):
                qs = DTModel.objects.filter(**{"start_datetime__%s__gt" % lookup: 2015})
                self.assertEqual(qs.count(), 1)
                self.assertEqual(str(qs.query).lower().count("extract"), 0)
                qs = DTModel.objects.filter(
                    **{"start_datetime__%s__gte" % lookup: 2015}
                )
                self.assertEqual(qs.count(), 2)
                self.assertEqual(str(qs.query).lower().count("extract"), 0)
                qs = DTModel.objects.annotate(
                    start_year=ExtractYear("start_datetime"),
                ).filter(**{"end_datetime__%s__gte" % lookup: F("start_year")})
                self.assertEqual(qs.count(), 1)
                self.assertGreaterEqual(str(qs.query).lower().count("extract"), 2)