def test_clear(self):
        self.assertSequenceEqual(
            TaggedItem.objects.order_by("tag"),
            [self.fatty, self.hairy, self.salty, self.yellow],
        )
        self.bacon.tags.clear()
        self.assertSequenceEqual(self.bacon.tags.all(), [])
        self.assertSequenceEqual(
            TaggedItem.objects.order_by("tag"),
            [self.hairy, self.yellow],
        )