def test_ticket2496(self):
        self.assertSequenceEqual(
            Item.objects.extra(tables=["queries_author"])
            .select_related()
            .order_by("name")[:1],
            [self.i4],
        )