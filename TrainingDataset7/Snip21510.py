def test_month_aggregation(self):
        self.assertEqual(
            Experiment.objects.aggregate(month_count=Count("assigned__month")),
            {"month_count": 1},
        )