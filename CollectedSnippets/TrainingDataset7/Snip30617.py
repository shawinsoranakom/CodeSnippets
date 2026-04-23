def test_ticket7076(self):
        # Excluding shouldn't eliminate NULL entries.
        self.assertSequenceEqual(
            Item.objects.exclude(modified=self.time1).order_by("name"),
            [self.i4, self.i3, self.i2],
        )
        self.assertSequenceEqual(
            Tag.objects.exclude(parent__name=self.t1.name),
            [self.t1, self.t4, self.t5],
        )