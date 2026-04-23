def test_tickets_6180_6203(self):
        # Dates with limits and/or counts
        self.assertEqual(Item.objects.count(), 4)
        self.assertEqual(Item.objects.datetimes("created", "month").count(), 1)
        self.assertEqual(Item.objects.datetimes("created", "day").count(), 2)
        self.assertEqual(len(Item.objects.datetimes("created", "day")), 2)
        self.assertEqual(
            Item.objects.datetimes("created", "day")[0],
            datetime.datetime(2007, 12, 19, 0, 0),
        )