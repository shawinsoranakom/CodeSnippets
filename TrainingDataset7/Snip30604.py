def test_ticket7096(self):
        # Make sure exclude() with multiple conditions continues to work.
        self.assertSequenceEqual(
            Tag.objects.filter(parent=self.t1, name="t3").order_by("name"),
            [self.t3],
        )
        self.assertSequenceEqual(
            Tag.objects.exclude(parent=self.t1, name="t3").order_by("name"),
            [self.t1, self.t2, self.t4, self.t5],
        )
        self.assertSequenceEqual(
            Item.objects.exclude(tags__name="t1", name="one")
            .order_by("name")
            .distinct(),
            [self.i4, self.i3, self.i2],
        )
        self.assertSequenceEqual(
            Item.objects.filter(name__in=["three", "four"])
            .exclude(tags__name="t1")
            .order_by("name"),
            [self.i4, self.i3],
        )

        # More twisted cases, involving nested negations.
        self.assertSequenceEqual(
            Item.objects.exclude(~Q(tags__name="t1", name="one")),
            [self.i1],
        )
        self.assertSequenceEqual(
            Item.objects.filter(~Q(tags__name="t1", name="one"), name="two"),
            [self.i2],
        )
        self.assertSequenceEqual(
            Item.objects.exclude(~Q(tags__name="t1", name="one"), name="two"),
            [self.i4, self.i1, self.i3],
        )