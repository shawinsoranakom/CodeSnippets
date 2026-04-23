def test_related_aggregates_m2m_and_fk(self):
        q = Q(friends__book__publisher__name="Apress") & ~Q(friends__name="test3")
        agg = Sum("friends__book__pages", filter=q)
        self.assertEqual(
            Author.objects.filter(name="test").aggregate(pages=agg)["pages"], 528
        )