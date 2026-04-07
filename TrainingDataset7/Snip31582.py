def test_fetch_mode_copied_fetching_many(self):
        specieses = list(
            Species.objects.fetch_mode(FETCH_PEERS).select_related("genus__family")
        )
        species = specieses[0]
        self.assertEqual(species._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            species.genus._state.fetch_mode,
            FETCH_PEERS,
        )
        self.assertEqual(
            species.genus.family._state.fetch_mode,
            FETCH_PEERS,
        )