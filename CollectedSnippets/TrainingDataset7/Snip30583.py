def test_tickets_5324_6704(self):
        self.assertSequenceEqual(
            Item.objects.filter(tags__name="t4"),
            [self.i4],
        )
        self.assertSequenceEqual(
            Item.objects.exclude(tags__name="t4").order_by("name").distinct(),
            [self.i1, self.i3, self.i2],
        )
        self.assertSequenceEqual(
            Item.objects.exclude(tags__name="t4").order_by("name").distinct().reverse(),
            [self.i2, self.i3, self.i1],
        )
        self.assertSequenceEqual(
            Author.objects.exclude(item__name="one").distinct().order_by("name"),
            [self.a2, self.a3, self.a4],
        )

        # Excluding across a m2m relation when there is more than one related
        # object associated was problematic.
        self.assertSequenceEqual(
            Item.objects.exclude(tags__name="t1").order_by("name"),
            [self.i4, self.i3],
        )
        self.assertSequenceEqual(
            Item.objects.exclude(tags__name="t1").exclude(tags__name="t4"),
            [self.i3],
        )

        # Excluding from a relation that cannot be NULL should not use outer
        # joins.
        query = Item.objects.exclude(creator__in=[self.a1, self.a2]).query
        self.assertNotIn(LOUTER, [x.join_type for x in query.alias_map.values()])

        # Similarly, when one of the joins cannot possibly, ever, involve NULL
        # values (Author -> ExtraInfo, in the following), it should never be
        # promoted to a left outer join. So the following query should only
        # involve one "left outer" join (Author -> Item is 0-to-many).
        qs = Author.objects.filter(id=self.a1.id).filter(
            Q(extra__note=self.n1) | Q(item__note=self.n3)
        )
        self.assertEqual(
            len(
                [
                    x
                    for x in qs.query.alias_map.values()
                    if x.join_type == LOUTER and qs.query.alias_refcount[x.table_alias]
                ]
            ),
            1,
        )

        # The previous changes shouldn't affect nullable foreign key joins.
        self.assertSequenceEqual(
            Tag.objects.filter(parent__isnull=True).order_by("name"), [self.t1]
        )
        self.assertSequenceEqual(
            Tag.objects.exclude(parent__isnull=True).order_by("name"),
            [self.t2, self.t3, self.t4, self.t5],
        )
        self.assertSequenceEqual(
            Tag.objects.exclude(Q(parent__name="t1") | Q(parent__isnull=True)).order_by(
                "name"
            ),
            [self.t4, self.t5],
        )
        self.assertSequenceEqual(
            Tag.objects.exclude(Q(parent__isnull=True) | Q(parent__name="t1")).order_by(
                "name"
            ),
            [self.t4, self.t5],
        )
        self.assertSequenceEqual(
            Tag.objects.exclude(Q(parent__parent__isnull=True)).order_by("name"),
            [self.t4, self.t5],
        )
        self.assertSequenceEqual(
            Tag.objects.filter(~Q(parent__parent__isnull=True)).order_by("name"),
            [self.t4, self.t5],
        )