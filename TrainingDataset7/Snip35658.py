def test_order_by_update_on_parent_unique_constraint(self):
        # Ordering by inherited fields is omitted because joined fields cannot
        # be used in the ORDER BY clause.
        UniqueNumberChild.objects.create(number=3)
        UniqueNumberChild.objects.create(number=4)
        with self.assertRaises(IntegrityError):
            UniqueNumberChild.objects.order_by("number").update(
                number=F("number") + 1,
            )