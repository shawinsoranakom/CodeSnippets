def test_case_aggregate(self):
        agg = Sum(
            Case(When(friends__age=40, then=F("friends__age"))),
            filter=Q(friends__name__startswith="test"),
        )
        self.assertEqual(Author.objects.aggregate(age=agg)["age"], 80)