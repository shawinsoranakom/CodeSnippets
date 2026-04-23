def test_related_filtering_query_efficiency_ticket_15844(self):
        r = Restaurant.objects.create(
            name="Guido's House of Pasta",
            address="944 W. Fullerton",
            serves_hot_dogs=True,
            serves_pizza=False,
        )
        s = Supplier.objects.create(restaurant=r)
        with self.assertNumQueries(1):
            self.assertSequenceEqual(Supplier.objects.filter(restaurant=r), [s])
        with self.assertNumQueries(1):
            self.assertSequenceEqual(r.supplier_set.all(), [s])