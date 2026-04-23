def test_queries_on_parent_access(self):
        italian_restaurant = ItalianRestaurant.objects.create(
            name="Guido's House of Pasta",
            address="944 W. Fullerton",
            serves_hot_dogs=True,
            serves_pizza=False,
            serves_gnocchi=True,
        )

        # No queries are made when accessing the parent objects.
        italian_restaurant = ItalianRestaurant.objects.get(pk=italian_restaurant.pk)
        with self.assertNumQueries(0):
            restaurant = italian_restaurant.restaurant_ptr
            self.assertEqual(restaurant.place_ptr.restaurant, restaurant)
            self.assertEqual(restaurant.italianrestaurant, italian_restaurant)

        # One query is made when accessing the parent objects when the instance
        # is deferred.
        italian_restaurant = ItalianRestaurant.objects.only("serves_gnocchi").get(
            pk=italian_restaurant.pk
        )
        with self.assertNumQueries(1):
            restaurant = italian_restaurant.restaurant_ptr
            self.assertEqual(restaurant.place_ptr.restaurant, restaurant)
            self.assertEqual(restaurant.italianrestaurant, italian_restaurant)

        # No queries are made when accessing the parent objects when the
        # instance has deferred a field not present in the parent table.
        italian_restaurant = ItalianRestaurant.objects.defer("serves_gnocchi").get(
            pk=italian_restaurant.pk
        )
        with self.assertNumQueries(0):
            restaurant = italian_restaurant.restaurant_ptr
            self.assertEqual(restaurant.place_ptr.restaurant, restaurant)
            self.assertEqual(restaurant.italianrestaurant, italian_restaurant)