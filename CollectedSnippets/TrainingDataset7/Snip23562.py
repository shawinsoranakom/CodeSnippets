def test_fetch_mode_copied_reverse_fetching_many(self):
        animals = list(Animal.objects.fetch_mode(FETCH_PEERS))
        animal = animals[0]
        self.assertEqual(animal._state.fetch_mode, FETCH_PEERS)
        tags = list(animal.tags.all())
        tag = tags[0]
        self.assertEqual(tag._state.fetch_mode, FETCH_PEERS)