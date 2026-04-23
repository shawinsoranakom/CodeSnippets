def test_ticket7155(self):
        # Nullable dates
        self.assertSequenceEqual(
            Item.objects.datetimes("modified", "day"),
            [datetime.datetime(2007, 12, 19, 0, 0)],
        )