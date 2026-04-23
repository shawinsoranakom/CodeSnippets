def test_remove(self):
        self.assertSequenceEqual(
            TaggedItem.objects.order_by("tag"),
            [self.fatty, self.hairy, self.salty, self.yellow],
        )
        self.bacon.tags.remove(self.fatty)
        self.assertSequenceEqual(self.bacon.tags.all(), [self.salty])
        self.assertSequenceEqual(
            TaggedItem.objects.order_by("tag"),
            [self.hairy, self.salty, self.yellow],
        )