def test_ordering_with_extra(self):
        # Ordering of extra() pieces is possible, too and you can mix extra
        # fields and model fields in the ordering.
        self.assertSequenceEqual(
            Ranking.objects.extra(
                tables=["django_site"], order_by=["-django_site.id", "rank"]
            ),
            [self.rank1, self.rank2, self.rank3],
        )

        sql = "case when %s > 2 then 1 else 0 end" % connection.ops.quote_name("rank")
        qs = Ranking.objects.extra(select={"good": sql})
        self.assertEqual(
            [o.good for o in qs.extra(order_by=("-good",))], [True, False, False]
        )
        self.assertSequenceEqual(
            qs.extra(order_by=("-good", "id")),
            [self.rank3, self.rank2, self.rank1],
        )

        # Despite having some extra aliases in the query, we can still omit
        # them in a values() query.
        dicts = qs.values("id", "rank").order_by("id")
        self.assertEqual([d["rank"] for d in dicts], [2, 1, 3])