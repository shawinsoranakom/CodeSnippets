def test_datetime_subquery_subtraction(self):
        subquery = Experiment.objects.filter(pk=OuterRef("pk")).values("start")
        queryset = Experiment.objects.annotate(
            difference=subquery - F("start"),
        ).filter(difference=datetime.timedelta())
        self.assertTrue(queryset.exists())