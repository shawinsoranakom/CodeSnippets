def test_ticket3037(self):
        self.assertSequenceEqual(
            Item.objects.filter(
                Q(creator__name="a3", name="two") | Q(creator__name="a4", name="four")
            ),
            [self.i4],
        )