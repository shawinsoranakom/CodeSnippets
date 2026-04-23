def test_aggregate_combined_lookup(self):
        expression = Cast(GreaterThan(F("year"), 1900), models.IntegerField())
        qs = Season.objects.aggregate(modern=models.Sum(expression))
        self.assertEqual(qs["modern"], 2)