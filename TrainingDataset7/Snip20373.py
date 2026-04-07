def test_extract_year_exact_lookup(self):
        """
        Extract year uses a BETWEEN filter to compare the year to allow indexes
        to be used.
        """
        start_datetime = datetime.datetime(2015, 6, 15, 14, 10)
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10)
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)

        for lookup in ("year", "iso_year"):
            with self.subTest(lookup):
                qs = DTModel.objects.filter(
                    **{"start_datetime__%s__exact" % lookup: 2015}
                )
                self.assertEqual(qs.count(), 1)
                query_string = str(qs.query).lower()
                self.assertEqual(query_string.count(" between "), 1)
                self.assertEqual(query_string.count("extract"), 0)
                # exact is implied and should be the same
                qs = DTModel.objects.filter(**{"start_datetime__%s" % lookup: 2015})
                self.assertEqual(qs.count(), 1)
                query_string = str(qs.query).lower()
                self.assertEqual(query_string.count(" between "), 1)
                self.assertEqual(query_string.count("extract"), 0)
                # date and datetime fields should behave the same
                qs = DTModel.objects.filter(**{"start_date__%s" % lookup: 2015})
                self.assertEqual(qs.count(), 1)
                query_string = str(qs.query).lower()
                self.assertEqual(query_string.count(" between "), 1)
                self.assertEqual(query_string.count("extract"), 0)
                # an expression rhs cannot use the between optimization.
                qs = DTModel.objects.annotate(
                    start_year=ExtractYear("start_datetime"),
                ).filter(end_datetime__year=F("start_year") + 1)
                self.assertEqual(qs.count(), 1)
                query_string = str(qs.query).lower()
                self.assertEqual(query_string.count(" between "), 0)
                self.assertEqual(query_string.count("extract"), 3)