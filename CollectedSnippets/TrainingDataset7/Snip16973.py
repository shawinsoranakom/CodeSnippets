def test_aggregation_expressions(self):
        a1 = Author.objects.aggregate(av_age=Sum("age") / Count("*"))
        a2 = Author.objects.aggregate(av_age=Sum("age") / Count("age"))
        a3 = Author.objects.aggregate(av_age=Avg("age"))
        self.assertEqual(a1, {"av_age": 37})
        self.assertEqual(a2, {"av_age": 37})
        self.assertEqual(a3, {"av_age": Approximate(37.4, places=1)})