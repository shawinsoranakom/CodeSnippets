def test_exclude_plain_distinct(self):
        """
        This should exclude Orders which have some items with status 1
        """
        self.assertSequenceEqual(
            Order.objects.exclude(items__status=1).distinct(),
            [self.o3],
        )