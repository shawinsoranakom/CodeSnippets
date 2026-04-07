def test_manager_all(self):
        # Restaurant.objects.all() just returns the Restaurants, not the
        # Places.
        self.assertSequenceEqual(Restaurant.objects.all(), [self.r1])
        # Place.objects.all() returns all Places, regardless of whether they
        # have Restaurants.
        self.assertSequenceEqual(Place.objects.order_by("name"), [self.p2, self.p1])