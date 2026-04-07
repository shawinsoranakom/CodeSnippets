def test_only_orders_with_all_items_having_status_1(self):
        """
        This should only return orders having ALL items set to status 1, or
        those items not having any orders at all. The correct way to write
        this query in SQL seems to be using two nested subqueries.
        """
        self.assertSequenceEqual(
            Order.objects.exclude(~Q(items__status=1)).distinct(),
            [self.o1],
        )