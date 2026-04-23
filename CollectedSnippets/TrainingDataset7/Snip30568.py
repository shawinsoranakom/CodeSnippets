def test_ticket4464(self):
        self.assertSequenceEqual(
            Item.objects.filter(tags=self.t1).filter(tags=self.t2),
            [self.i1],
        )
        self.assertSequenceEqual(
            Item.objects.filter(tags__in=[self.t1, self.t2])
            .distinct()
            .order_by("name"),
            [self.i1, self.i2],
        )
        self.assertSequenceEqual(
            Item.objects.filter(tags__in=[self.t1, self.t2]).filter(tags=self.t3),
            [self.i2],
        )

        # Make sure .distinct() works with slicing (this was broken in Oracle).
        self.assertSequenceEqual(
            Item.objects.filter(tags__in=[self.t1, self.t2]).order_by("name")[:3],
            [self.i1, self.i1, self.i2],
        )
        self.assertSequenceEqual(
            Item.objects.filter(tags__in=[self.t1, self.t2])
            .distinct()
            .order_by("name")[:3],
            [self.i1, self.i2],
        )