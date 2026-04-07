def test_aggregate_over_annotation(self):
        agg = Author.objects.annotate(other_age=F("age")).aggregate(
            otherage_sum=Sum("other_age")
        )
        other_agg = Author.objects.aggregate(age_sum=Sum("age"))
        self.assertEqual(agg["otherage_sum"], other_agg["age_sum"])