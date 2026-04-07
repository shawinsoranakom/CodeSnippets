def test_inheritance_select_related(self):
        # Regression test for #7246
        r1 = Restaurant.objects.create(
            name="Nobu", serves_hot_dogs=True, serves_pizza=False
        )
        r2 = Restaurant.objects.create(
            name="Craft", serves_hot_dogs=False, serves_pizza=True
        )
        Supplier.objects.create(name="John", restaurant=r1)
        Supplier.objects.create(name="Jane", restaurant=r2)

        self.assertQuerySetEqual(
            Supplier.objects.order_by("name").select_related(),
            [
                "Jane",
                "John",
            ],
            attrgetter("name"),
        )

        jane = Supplier.objects.order_by("name").select_related("restaurant")[0]
        self.assertEqual(jane.restaurant.name, "Craft")