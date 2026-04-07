def test_date_subquery_subtraction(self):
        subquery = Experiment.objects.filter(pk=OuterRef("pk")).values("completed")
        queryset = Experiment.objects.annotate(
            difference=subquery - F("completed"),
        ).filter(difference=datetime.timedelta())
        self.assertTrue(queryset.exists())