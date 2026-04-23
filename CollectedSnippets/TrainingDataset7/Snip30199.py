def test_nested_prefetch_related_with_duplicate_prefetch_and_depth(self):
        people = Person.objects.prefetch_related(
            Prefetch(
                "houses__main_room",
                queryset=Room.objects.filter(name="Dining room"),
                to_attr="dining_room",
            ),
            "houses__main_room",
        )
        with self.assertNumQueries(4):
            main_room = people[0].houses.all()[0]

        people = Person.objects.prefetch_related(
            "houses__main_room",
            Prefetch(
                "houses__main_room",
                queryset=Room.objects.filter(name="Dining room"),
                to_attr="dining_room",
            ),
        )
        with self.assertNumQueries(4):
            main_room = people[0].houses.all()[0]

        self.assertEqual(main_room.main_room, self.room1_1)