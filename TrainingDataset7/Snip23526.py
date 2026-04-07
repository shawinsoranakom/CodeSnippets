def test_assign(self):
        bacon = Vegetable.objects.create(name="Bacon", is_yucky=False)
        fatty = bacon.tags.create(tag="fatty")
        salty = bacon.tags.create(tag="salty")

        bacon.tags.set([fatty, salty])
        self.assertSequenceEqual(bacon.tags.all(), [fatty, salty])

        bacon.tags.set([fatty])
        self.assertSequenceEqual(bacon.tags.all(), [fatty])

        bacon.tags.set([])
        self.assertSequenceEqual(bacon.tags.all(), [])