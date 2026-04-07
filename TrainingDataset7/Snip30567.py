def test_ticket2306(self):
        # Checking that no join types are "left outer" joins.
        query = Item.objects.filter(tags=self.t2).query
        self.assertNotIn(LOUTER, [x.join_type for x in query.alias_map.values()])

        self.assertSequenceEqual(
            Item.objects.filter(Q(tags=self.t1)).order_by("name"),
            [self.i1, self.i2],
        )
        self.assertSequenceEqual(
            Item.objects.filter(Q(tags=self.t1)).filter(Q(tags=self.t2)),
            [self.i1],
        )
        self.assertSequenceEqual(
            Item.objects.filter(Q(tags=self.t1)).filter(
                Q(creator__name="fred") | Q(tags=self.t2)
            ),
            [self.i1],
        )

        # Each filter call is processed "at once" against a single table, so
        # this is different from the previous example as it tries to find tags
        # that are two things at once (rather than two tags).
        self.assertSequenceEqual(
            Item.objects.filter(Q(tags=self.t1) & Q(tags=self.t2)), []
        )
        self.assertSequenceEqual(
            Item.objects.filter(
                Q(tags=self.t1), Q(creator__name="fred") | Q(tags=self.t2)
            ),
            [],
        )

        qs = Author.objects.filter(ranking__rank=2, ranking__id=self.rank1.id)
        self.assertSequenceEqual(list(qs), [self.a2])
        self.assertEqual(2, qs.query.count_active_tables(), 2)
        qs = Author.objects.filter(ranking__rank=2).filter(ranking__id=self.rank1.id)
        self.assertEqual(qs.query.count_active_tables(), 3)