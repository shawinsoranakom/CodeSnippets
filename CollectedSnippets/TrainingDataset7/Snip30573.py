def test_ticket2253(self):
        q1 = Item.objects.order_by("name")
        q2 = Item.objects.filter(id=self.i1.id)
        self.assertSequenceEqual(q1, [self.i4, self.i1, self.i3, self.i2])
        self.assertSequenceEqual(q2, [self.i1])
        self.assertSequenceEqual(
            (q1 | q2).order_by("name"),
            [self.i4, self.i1, self.i3, self.i2],
        )
        self.assertSequenceEqual((q1 & q2).order_by("name"), [self.i1])

        q1 = Item.objects.filter(tags=self.t1)
        q2 = Item.objects.filter(note=self.n3, tags=self.t2)
        q3 = Item.objects.filter(creator=self.a4)
        self.assertSequenceEqual(
            ((q1 & q2) | q3).order_by("name"),
            [self.i4, self.i1],
        )