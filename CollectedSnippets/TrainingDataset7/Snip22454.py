def test_fetch_mode_copied_reverse_fetching_many(self):
        countries = list(Country.objects.fetch_mode(FETCH_PEERS))
        country = countries[0]
        self.assertEqual(country._state.fetch_mode, FETCH_PEERS)
        person = country.person_set.earliest("pk")
        self.assertEqual(
            person._state.fetch_mode,
            FETCH_PEERS,
        )