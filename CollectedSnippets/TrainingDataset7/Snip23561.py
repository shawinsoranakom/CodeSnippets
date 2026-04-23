def test_fetch_mode_copied_reverse_fetching_one(self):
        animal = Animal.objects.fetch_mode(FETCH_PEERS).get(pk=self.lion.pk)
        self.assertEqual(animal._state.fetch_mode, FETCH_PEERS)
        tag = animal.tags.get(tag="yellow")
        self.assertEqual(tag._state.fetch_mode, FETCH_PEERS)