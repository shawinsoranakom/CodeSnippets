def test_fetch_mode_copied_forward_fetching_many(self):
        people = list(Person.objects.fetch_mode(FETCH_PEERS))
        person = people[0]
        self.assertEqual(person._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            person.person_country._state.fetch_mode,
            FETCH_PEERS,
        )