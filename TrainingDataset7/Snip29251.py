def test_getter(self):
        # A Restaurant can access its place.
        self.assertEqual(repr(self.r1.place), "<Place: Demon Dogs the place>")
        # A Place can access its restaurant, if available.
        self.assertEqual(
            repr(self.p1.restaurant), "<Restaurant: Demon Dogs the restaurant>"
        )
        # p2 doesn't have an associated restaurant.
        with self.assertRaisesMessage(
            Restaurant.DoesNotExist, "Place has no restaurant"
        ):
            self.p2.restaurant
        # The exception raised on attribute access when a related object
        # doesn't exist should be an instance of a subclass of `AttributeError`
        # refs #21563
        self.assertFalse(hasattr(self.p2, "restaurant"))