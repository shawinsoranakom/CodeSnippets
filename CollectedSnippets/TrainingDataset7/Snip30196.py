def test_custom_qs(self):
        # Test basic.
        with self.assertNumQueries(2):
            lst1 = list(Person.objects.prefetch_related("houses"))
        with self.assertNumQueries(2):
            lst2 = list(
                Person.objects.prefetch_related(
                    Prefetch(
                        "houses", queryset=House.objects.all(), to_attr="houses_lst"
                    )
                )
            )
        self.assertEqual(
            self.traverse_qs(lst1, [["houses"]]),
            self.traverse_qs(lst2, [["houses_lst"]]),
        )

        # Test queryset filtering.
        with self.assertNumQueries(2):
            lst2 = list(
                Person.objects.prefetch_related(
                    Prefetch(
                        "houses",
                        queryset=House.objects.filter(
                            pk__in=[self.house1.pk, self.house3.pk]
                        ),
                        to_attr="houses_lst",
                    )
                )
            )
        self.assertEqual(len(lst2[0].houses_lst), 1)
        self.assertEqual(lst2[0].houses_lst[0], self.house1)
        self.assertEqual(len(lst2[1].houses_lst), 1)
        self.assertEqual(lst2[1].houses_lst[0], self.house3)

        # Test flattened.
        with self.assertNumQueries(3):
            lst1 = list(Person.objects.prefetch_related("houses__rooms"))
        with self.assertNumQueries(3):
            lst2 = list(
                Person.objects.prefetch_related(
                    Prefetch(
                        "houses__rooms",
                        queryset=Room.objects.all(),
                        to_attr="rooms_lst",
                    )
                )
            )
        self.assertEqual(
            self.traverse_qs(lst1, [["houses", "rooms"]]),
            self.traverse_qs(lst2, [["houses", "rooms_lst"]]),
        )

        # Test inner select_related.
        with self.assertNumQueries(3):
            lst1 = list(Person.objects.prefetch_related("houses__owner"))
        with self.assertNumQueries(2):
            lst2 = list(
                Person.objects.prefetch_related(
                    Prefetch("houses", queryset=House.objects.select_related("owner"))
                )
            )
        self.assertEqual(
            self.traverse_qs(lst1, [["houses", "owner"]]),
            self.traverse_qs(lst2, [["houses", "owner"]]),
        )

        # Test inner prefetch.
        inner_rooms_qs = Room.objects.filter(pk__in=[self.room1_1.pk, self.room1_2.pk])
        houses_qs_prf = House.objects.prefetch_related(
            Prefetch("rooms", queryset=inner_rooms_qs, to_attr="rooms_lst")
        )
        with self.assertNumQueries(4):
            lst2 = list(
                Person.objects.prefetch_related(
                    Prefetch(
                        "houses",
                        queryset=houses_qs_prf.filter(pk=self.house1.pk),
                        to_attr="houses_lst",
                    ),
                    Prefetch("houses_lst__rooms_lst__main_room_of"),
                )
            )

        self.assertEqual(len(lst2[0].houses_lst[0].rooms_lst), 2)
        self.assertEqual(lst2[0].houses_lst[0].rooms_lst[0], self.room1_1)
        self.assertEqual(lst2[0].houses_lst[0].rooms_lst[1], self.room1_2)
        self.assertEqual(lst2[0].houses_lst[0].rooms_lst[0].main_room_of, self.house1)
        self.assertEqual(len(lst2[1].houses_lst), 0)

        # Test ForwardManyToOneDescriptor.
        houses = House.objects.select_related("owner")
        with self.assertNumQueries(6):
            rooms = Room.objects.prefetch_related("house")
            lst1 = self.traverse_qs(rooms, [["house", "owner"]])
        with self.assertNumQueries(2):
            rooms = Room.objects.prefetch_related(Prefetch("house", queryset=houses))
            lst2 = self.traverse_qs(rooms, [["house", "owner"]])
        self.assertEqual(lst1, lst2)
        with self.assertNumQueries(2):
            houses = House.objects.select_related("owner")
            rooms = Room.objects.prefetch_related(
                Prefetch("house", queryset=houses, to_attr="house_attr")
            )
            lst2 = self.traverse_qs(rooms, [["house_attr", "owner"]])
        self.assertEqual(lst1, lst2)
        room = Room.objects.prefetch_related(
            Prefetch("house", queryset=houses.filter(address="DoesNotExist"))
        ).first()
        with self.assertRaises(ObjectDoesNotExist):
            getattr(room, "house")
        room = Room.objects.prefetch_related(
            Prefetch(
                "house",
                queryset=houses.filter(address="DoesNotExist"),
                to_attr="house_attr",
            )
        ).first()
        self.assertIsNone(room.house_attr)
        rooms = Room.objects.prefetch_related(
            Prefetch("house", queryset=House.objects.only("name"))
        )
        with self.assertNumQueries(2):
            getattr(rooms.first().house, "name")
        with self.assertNumQueries(3):
            getattr(rooms.first().house, "address")

        # Test ReverseOneToOneDescriptor.
        houses = House.objects.select_related("owner")
        with self.assertNumQueries(6):
            rooms = Room.objects.prefetch_related("main_room_of")
            lst1 = self.traverse_qs(rooms, [["main_room_of", "owner"]])
        with self.assertNumQueries(2):
            rooms = Room.objects.prefetch_related(
                Prefetch("main_room_of", queryset=houses)
            )
            lst2 = self.traverse_qs(rooms, [["main_room_of", "owner"]])
        self.assertEqual(lst1, lst2)
        with self.assertNumQueries(2):
            rooms = list(
                Room.objects.prefetch_related(
                    Prefetch(
                        "main_room_of",
                        queryset=houses,
                        to_attr="main_room_of_attr",
                    )
                )
            )
            lst2 = self.traverse_qs(rooms, [["main_room_of_attr", "owner"]])
        self.assertEqual(lst1, lst2)
        room = (
            Room.objects.filter(main_room_of__isnull=False)
            .prefetch_related(
                Prefetch("main_room_of", queryset=houses.filter(address="DoesNotExist"))
            )
            .first()
        )
        with self.assertRaises(ObjectDoesNotExist):
            getattr(room, "main_room_of")
        room = (
            Room.objects.filter(main_room_of__isnull=False)
            .prefetch_related(
                Prefetch(
                    "main_room_of",
                    queryset=houses.filter(address="DoesNotExist"),
                    to_attr="main_room_of_attr",
                )
            )
            .first()
        )
        self.assertIsNone(room.main_room_of_attr)

        # The custom queryset filters should be applied to the queryset
        # instance returned by the manager.
        person = Person.objects.prefetch_related(
            Prefetch("houses", queryset=House.objects.filter(name="House 1")),
        ).get(pk=self.person1.pk)
        self.assertEqual(
            list(person.houses.all()),
            list(person.houses.all().all()),
        )