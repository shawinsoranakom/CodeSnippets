def test_nested_prefetch_related_are_not_overwritten(self):
        # Regression test for #24873
        houses_2 = House.objects.prefetch_related(Prefetch("rooms"))
        persons = Person.objects.prefetch_related(Prefetch("houses", queryset=houses_2))
        houses = House.objects.prefetch_related(Prefetch("occupants", queryset=persons))
        list(houses)  # queryset must be evaluated once to reproduce the bug.
        self.assertEqual(
            houses.all()[0].occupants.all()[0].houses.all()[1].rooms.all()[0],
            self.room2_1,
        )