def test_fetch_mode_copied_fetching_one(self):
        fly = (
            Species.objects.fetch_mode(FETCH_PEERS)
            .select_related("genus__family")
            .get(name="melanogaster")
        )
        self.assertEqual(fly._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            fly.genus._state.fetch_mode,
            FETCH_PEERS,
        )
        self.assertEqual(
            fly.genus.family._state.fetch_mode,
            FETCH_PEERS,
        )