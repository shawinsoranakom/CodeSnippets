def test_create_diamond_mti_common_parent(self):
        with self.assertNumQueries(4):
            italian_restaurant_child = ItalianRestaurantCommonParent.objects.create(
                name="Ristorante Miron",
                address="1234 W. Ash",
            )

        self.assertEqual(
            italian_restaurant_child.italianrestaurant_ptr.place_ptr,
            italian_restaurant_child.place_ptr_two,
        )
        self.assertEqual(
            italian_restaurant_child.italianrestaurant_ptr.restaurant_ptr,
            italian_restaurant_child.restaurant_ptr,
        )
        self.assertEqual(
            italian_restaurant_child.restaurant_ptr.place_ptr,
            italian_restaurant_child.place_ptr_two,
        )
        self.assertEqual(italian_restaurant_child.name, "Ristorante Miron")
        self.assertEqual(italian_restaurant_child.address, "1234 W. Ash")