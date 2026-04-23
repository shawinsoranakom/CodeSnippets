def test_exclude_with_q_object_no_distinct(self):
        """
        This should exclude Orders which have some items with status 1
        """
        self.assertSequenceEqual(
            Order.objects.exclude(Q(items__status=1)),
            [self.o3],
        )