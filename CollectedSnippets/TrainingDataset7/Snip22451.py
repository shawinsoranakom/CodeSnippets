def test_fetch_mode_copied_forward_fetching_one(self):
        person = Person.objects.fetch_mode(FETCH_PEERS).get(pk=self.bob.pk)
        self.assertEqual(person._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            person.person_country._state.fetch_mode,
            FETCH_PEERS,
        )