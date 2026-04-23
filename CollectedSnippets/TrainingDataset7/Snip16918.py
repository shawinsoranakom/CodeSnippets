def test_filtered_aggregate_ref_annotation(self):
        aggs = Author.objects.annotate(double_age=F("age") * 2).aggregate(
            cnt=Count("pk", filter=Q(double_age__gt=100)),
        )
        self.assertEqual(aggs["cnt"], 2)