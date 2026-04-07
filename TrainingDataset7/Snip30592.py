def test_tickets_2076_7256(self):
        # Ordering on related tables should be possible, even if the table is
        # not otherwise involved.
        self.assertSequenceEqual(
            Item.objects.order_by("note__note", "name"),
            [self.i2, self.i4, self.i1, self.i3],
        )

        # Ordering on a related field should use the remote model's default
        # ordering as a final step.
        self.assertSequenceEqual(
            Author.objects.order_by("extra", "-name"),
            [self.a2, self.a1, self.a4, self.a3],
        )

        # Using remote model default ordering can span multiple models (in this
        # case, Cover is ordered by Item's default, which uses Note's default).
        self.assertSequenceEqual(Cover.objects.all(), [self.c1, self.c2])

        # If the remote model does not have a default ordering, we order by its
        # 'id' field.
        self.assertSequenceEqual(
            Item.objects.order_by("creator", "name"),
            [self.i1, self.i3, self.i2, self.i4],
        )

        # Ordering by a many-valued attribute (e.g. a many-to-many or reverse
        # ForeignKey) is legal, but the results might not make sense. That
        # isn't Django's problem. Garbage in, garbage out.
        self.assertSequenceEqual(
            Item.objects.filter(tags__isnull=False).order_by("tags", "id"),
            [self.i1, self.i2, self.i1, self.i2, self.i4],
        )

        # If we replace the default ordering, Django adjusts the required
        # tables automatically. Item normally requires a join with Note to do
        # the default ordering, but that isn't needed here.
        qs = Item.objects.order_by("name")
        self.assertSequenceEqual(qs, [self.i4, self.i1, self.i3, self.i2])
        self.assertEqual(len(qs.query.alias_map), 1)