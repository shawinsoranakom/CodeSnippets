def test_empty_count(self):
        """
        Testing that PostGISAdapter.__eq__ does check empty strings. See
        #13670.
        """
        # contrived example, but need a geo lookup paired with an id__in lookup
        pueblo = City.objects.get(name="Pueblo")
        state = State.objects.filter(poly__contains=pueblo.point)
        cities_within_state = City.objects.filter(id__in=state)

        # .count() should not throw TypeError in __eq__
        self.assertEqual(cities_within_state.count(), 1)