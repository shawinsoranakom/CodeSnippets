def test_fetch_mode_copied_reverse_fetching_one(self):
        country = Country.objects.fetch_mode(FETCH_PEERS).get(pk=self.usa.pk)
        self.assertEqual(country._state.fetch_mode, FETCH_PEERS)
        person = country.person_set.get(pk=self.bob.pk)
        self.assertEqual(
            person._state.fetch_mode,
            FETCH_PEERS,
        )