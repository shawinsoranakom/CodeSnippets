def test_fetch_mode_copied_reverse_fetching_one(self):
        p1 = Place.objects.fetch_mode(FETCH_PEERS).get(pk=self.p1.pk)
        self.assertEqual(p1._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            p1.restaurant._state.fetch_mode,
            FETCH_PEERS,
        )