def test_fetch_mode_copied_forward_fetching_one(self):
        r1 = Restaurant.objects.fetch_mode(FETCH_PEERS).get(pk=self.r1.pk)
        self.assertEqual(r1._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            r1.place._state.fetch_mode,
            FETCH_PEERS,
        )