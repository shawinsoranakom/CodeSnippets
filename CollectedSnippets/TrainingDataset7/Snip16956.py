def test_avg_duration_field(self):
        # Explicit `output_field`.
        self.assertEqual(
            Publisher.objects.aggregate(Avg("duration", output_field=DurationField())),
            {"duration__avg": datetime.timedelta(days=1, hours=12)},
        )
        # Implicit `output_field`.
        self.assertEqual(
            Publisher.objects.aggregate(Avg("duration")),
            {"duration__avg": datetime.timedelta(days=1, hours=12)},
        )