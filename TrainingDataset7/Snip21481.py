def test_time_subquery_subtraction(self):
        Time.objects.create(time=datetime.time(12, 30, 15, 2345))
        subquery = Time.objects.filter(pk=OuterRef("pk")).values("time")
        queryset = Time.objects.annotate(
            difference=subquery - F("time"),
        ).filter(difference=datetime.timedelta())
        self.assertTrue(queryset.exists())