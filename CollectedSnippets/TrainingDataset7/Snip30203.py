def test_to_attr_cached_property(self):
        persons = Person.objects.prefetch_related(
            Prefetch("houses", House.objects.all(), to_attr="cached_all_houses"),
        )
        for person in persons:
            # To bypass caching at the related descriptor level, don't use
            # person.houses.all() here.
            all_houses = list(House.objects.filter(occupants=person))
            with self.assertNumQueries(0):
                self.assertEqual(person.cached_all_houses, all_houses)