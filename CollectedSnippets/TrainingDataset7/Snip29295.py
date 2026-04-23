def test_fetch_mode_copied_forward_fetching_many(self):
        Restaurant.objects.create(
            place=self.p2, serves_hot_dogs=True, serves_pizza=False
        )
        r1, r2 = Restaurant.objects.fetch_mode(FETCH_PEERS)
        self.assertEqual(r1._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            r1.place._state.fetch_mode,
            FETCH_PEERS,
        )