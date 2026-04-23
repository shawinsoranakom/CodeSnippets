def test_tickets_7448_7707(self):
        # Complex objects should be converted to strings before being used in
        # lookups.
        self.assertSequenceEqual(
            Item.objects.filter(created__in=[self.time1, self.time2]),
            [self.i1, self.i2],
        )