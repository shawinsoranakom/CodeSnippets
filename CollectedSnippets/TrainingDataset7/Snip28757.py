def test_parent_access_copies_fetch_mode(self):
        italian_restaurant = ItalianRestaurant.objects.create(
            name="Mom's Spaghetti",
            address="2131 Woodward Ave",
            serves_hot_dogs=False,
            serves_pizza=False,
            serves_gnocchi=True,
        )

        # No queries are made when accessing the parent objects.
        italian_restaurant = ItalianRestaurant.objects.fetch_mode(FETCH_PEERS).get(
            pk=italian_restaurant.pk
        )
        restaurant = italian_restaurant.restaurant_ptr
        self.assertEqual(restaurant._state.fetch_mode, FETCH_PEERS)