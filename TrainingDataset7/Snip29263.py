def test_assign_none_to_null_cached_reverse_relation(self):
        p = Place.objects.get(name="Demon Dogs")
        # Prime the relation's cache with a value of None.
        with self.assertRaises(Place.undergroundbar.RelatedObjectDoesNotExist):
            getattr(p, "undergroundbar")
        # Assigning None works if there isn't a related UndergroundBar and the
        # reverse cache has a value of None.
        p.undergroundbar = None