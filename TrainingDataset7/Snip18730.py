def test_aggregation(self):
        """Raise NotSupportedError when aggregating on date/time fields."""
        for aggregate in (Sum, Avg, Variance, StdDev):
            msg = (
                f"SQLite does not support {aggregate.__name__} on date or "
                "time fields, because they are stored as text."
            )
            with self.assertRaisesMessage(NotSupportedError, msg):
                Item.objects.aggregate(aggregate("time"))
            with self.assertRaisesMessage(NotSupportedError, msg):
                Item.objects.aggregate(aggregate("date"))
            with self.assertRaisesMessage(NotSupportedError, msg):
                Item.objects.aggregate(aggregate("last_modified"))
            with self.assertRaisesMessage(NotSupportedError, msg):
                Item.objects.aggregate(
                    **{
                        "complex": aggregate("last_modified")
                        + aggregate("last_modified")
                    }
                )