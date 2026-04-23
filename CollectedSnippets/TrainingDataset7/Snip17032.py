def test_aggregation_default_after_annotation(self):
        result = Publisher.objects.annotate(
            double_num_awards=F("num_awards") * 2,
        ).aggregate(value=Sum("double_num_awards", default=0))
        self.assertEqual(result["value"], 40)