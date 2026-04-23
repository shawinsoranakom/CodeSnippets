def test_related_aggregates_m2m(self):
        agg = Sum("friends__age", filter=~Q(friends__name="test"))
        self.assertEqual(
            Author.objects.filter(name="test").aggregate(age=agg)["age"], 160
        )