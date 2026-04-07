def test_sum_duration_field(self):
        self.assertEqual(
            Publisher.objects.aggregate(Sum("duration", output_field=DurationField())),
            {"duration__sum": datetime.timedelta(days=3)},
        )