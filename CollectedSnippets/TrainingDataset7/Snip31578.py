def test_reverse_relation_caching(self):
        species = (
            Species.objects.select_related("genus").filter(name="melanogaster").first()
        )
        with self.assertNumQueries(0):
            self.assertEqual(species.genus.name, "Drosophila")
        # The species_set reverse relation isn't cached.
        self.assertEqual(species.genus._state.fields_cache, {})
        with self.assertNumQueries(1):
            self.assertEqual(species.genus.species_set.first().name, "melanogaster")