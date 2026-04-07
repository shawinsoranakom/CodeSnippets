def test_related_objects_for_inherited_models(self):
        # Related objects work just as they normally do.
        s1 = Supplier.objects.create(name="Joe's Chickens", address="123 Sesame St")
        s1.customers.set([self.restaurant, self.italian_restaurant])
        s2 = Supplier.objects.create(name="Luigi's Pasta", address="456 Sesame St")
        s2.customers.set([self.italian_restaurant])

        # This won't work because the Place we select is not a Restaurant (it's
        # a Supplier).
        p = Place.objects.get(name="Joe's Chickens")
        with self.assertRaises(Restaurant.DoesNotExist):
            p.restaurant

        self.assertEqual(p.supplier, s1)
        self.assertQuerySetEqual(
            self.italian_restaurant.provider.order_by("-name"),
            ["Luigi's Pasta", "Joe's Chickens"],
            attrgetter("name"),
        )
        self.assertQuerySetEqual(
            Restaurant.objects.filter(provider__name__contains="Chickens"),
            [
                "Ristorante Miron",
                "Demon Dogs",
            ],
            attrgetter("name"),
        )
        self.assertQuerySetEqual(
            ItalianRestaurant.objects.filter(provider__name__contains="Chickens"),
            [
                "Ristorante Miron",
            ],
            attrgetter("name"),
        )

        ParkingLot.objects.create(name="Main St", address="111 Main St", main_site=s1)
        ParkingLot.objects.create(
            name="Well Lit", address="124 Sesame St", main_site=self.italian_restaurant
        )

        self.assertEqual(
            Restaurant.objects.get(lot__name="Well Lit").name, "Ristorante Miron"
        )