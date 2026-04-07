def test_values_in_subquery(self):
        # If a values() queryset is used, then the given values
        # will be used instead of forcing use of the relation's field.
        o1 = Order.objects.create(id=-2)
        o2 = Order.objects.create(id=-1)
        oi1 = OrderItem.objects.create(order=o1, status=0)
        oi1.status = oi1.pk
        oi1.save()
        OrderItem.objects.create(order=o2, status=0)

        # The query below should match o1 as it has related order_item
        # with id == status.
        self.assertSequenceEqual(
            Order.objects.filter(items__in=OrderItem.objects.values_list("status")),
            [o1],
        )