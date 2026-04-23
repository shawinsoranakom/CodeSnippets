def test_aggregation_default_using_duration_from_python(self):
        result = Publisher.objects.filter(num_awards__gt=3).aggregate(
            value=Sum("duration", default=datetime.timedelta(0)),
        )
        self.assertEqual(result["value"], datetime.timedelta(0))