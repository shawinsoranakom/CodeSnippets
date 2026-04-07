def test_fetch_mode_copied_reverse_fetching_many(self):
        Restaurant.objects.create(
            place=self.p2, serves_hot_dogs=True, serves_pizza=False
        )
        p1, p2 = Place.objects.fetch_mode(FETCH_PEERS)
        self.assertEqual(p1._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            p1.restaurant._state.fetch_mode,
            FETCH_PEERS,
        )