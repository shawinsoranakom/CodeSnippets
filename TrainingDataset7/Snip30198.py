def test_nested_prefetch_related_with_duplicate_prefetcher(self):
        """
        Nested prefetches whose name clashes with descriptor names
        (Person.houses here) are allowed.
        """
        occupants = Person.objects.prefetch_related(
            Prefetch("houses", to_attr="some_attr_name"),
            Prefetch("houses", queryset=House.objects.prefetch_related("main_room")),
        )
        houses = House.objects.prefetch_related(
            Prefetch("occupants", queryset=occupants)
        )
        with self.assertNumQueries(5):
            self.traverse_qs(list(houses), [["occupants", "houses", "main_room"]])