def test_id_field_update_on_ancestor_change(self):
        place1 = Place.objects.create(name="House of Pasta", address="944 Fullerton")
        place2 = Place.objects.create(name="House of Pizza", address="954 Fullerton")
        place3 = Place.objects.create(name="Burger house", address="964 Fullerton")
        restaurant1 = Restaurant.objects.create(
            place_ptr=place1,
            serves_hot_dogs=True,
            serves_pizza=False,
        )
        restaurant2 = Restaurant.objects.create(
            place_ptr=place2,
            serves_hot_dogs=True,
            serves_pizza=False,
        )

        italian_restaurant = ItalianRestaurant.objects.create(
            restaurant_ptr=restaurant1,
            serves_gnocchi=True,
        )
        # Changing the parent of a restaurant changes the restaurant's ID & PK.
        restaurant1.place_ptr = place3
        self.assertEqual(restaurant1.pk, place3.pk)
        self.assertEqual(restaurant1.id, place3.id)
        self.assertEqual(restaurant1.pk, restaurant1.id)
        restaurant1.place_ptr = None
        self.assertIsNone(restaurant1.pk)
        self.assertIsNone(restaurant1.id)
        # Changing the parent of an italian restaurant changes the restaurant's
        # ID & PK.
        italian_restaurant.restaurant_ptr = restaurant2
        self.assertEqual(italian_restaurant.pk, restaurant2.pk)
        self.assertEqual(italian_restaurant.id, restaurant2.id)
        self.assertEqual(italian_restaurant.pk, italian_restaurant.id)
        italian_restaurant.restaurant_ptr = None
        self.assertIsNone(italian_restaurant.pk)
        self.assertIsNone(italian_restaurant.id)