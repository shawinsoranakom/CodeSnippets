def test_aggregation_default_using_duration_from_database(self):
        result = Publisher.objects.filter(num_awards__gt=3).aggregate(
            value=Sum("duration", default=Now() - Now()),
        )
        self.assertEqual(result["value"], datetime.timedelta(0))