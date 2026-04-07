def test_ticket8597(self):
        # Regression tests for case-insensitive comparisons
        item_ab = Item.objects.create(
            name="a_b", created=datetime.datetime.now(), creator=self.a2, note=self.n1
        )
        item_xy = Item.objects.create(
            name="x%y", created=datetime.datetime.now(), creator=self.a2, note=self.n1
        )
        self.assertSequenceEqual(
            Item.objects.filter(name__iexact="A_b"),
            [item_ab],
        )
        self.assertSequenceEqual(
            Item.objects.filter(name__iexact="x%Y"),
            [item_xy],
        )
        self.assertSequenceEqual(
            Item.objects.filter(name__istartswith="A_b"),
            [item_ab],
        )
        self.assertSequenceEqual(
            Item.objects.filter(name__iendswith="A_b"),
            [item_ab],
        )