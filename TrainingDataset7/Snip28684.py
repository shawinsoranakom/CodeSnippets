def test_meta_fields_and_ordering(self):
        # Make sure Restaurant and ItalianRestaurant have the right fields in
        # the right order.
        self.assertEqual(
            [f.name for f in Restaurant._meta.fields],
            [
                "id",
                "name",
                "address",
                "place_ptr",
                "rating",
                "serves_hot_dogs",
                "serves_pizza",
                "chef",
            ],
        )
        self.assertEqual(
            [f.name for f in ItalianRestaurant._meta.fields],
            [
                "id",
                "name",
                "address",
                "place_ptr",
                "rating",
                "serves_hot_dogs",
                "serves_pizza",
                "chef",
                "restaurant_ptr",
                "serves_gnocchi",
            ],
        )
        self.assertEqual(Restaurant._meta.ordering, ["-rating"])