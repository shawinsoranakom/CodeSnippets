def test_ticket1050(self):
        self.assertSequenceEqual(
            Item.objects.filter(tags__isnull=True),
            [self.i3],
        )
        self.assertSequenceEqual(
            Item.objects.filter(tags__id__isnull=True),
            [self.i3],
        )