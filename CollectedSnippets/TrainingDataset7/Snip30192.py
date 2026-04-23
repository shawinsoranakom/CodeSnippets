def test_o2m_through_m2m(self):
        # Control lookups.
        with self.assertNumQueries(3):
            lst1 = self.traverse_qs(
                Person.objects.prefetch_related("houses", "houses__rooms"),
                [["houses", "rooms"]],
            )

        # Test lookups.
        with self.assertNumQueries(3):
            lst2 = self.traverse_qs(
                Person.objects.prefetch_related(Prefetch("houses"), "houses__rooms"),
                [["houses", "rooms"]],
            )
        self.assertEqual(lst1, lst2)
        with self.assertNumQueries(3):
            lst2 = self.traverse_qs(
                Person.objects.prefetch_related(
                    Prefetch("houses"), Prefetch("houses__rooms")
                ),
                [["houses", "rooms"]],
            )
        self.assertEqual(lst1, lst2)
        with self.assertNumQueries(3):
            lst2 = self.traverse_qs(
                Person.objects.prefetch_related(
                    Prefetch("houses", to_attr="houses_lst"), "houses_lst__rooms"
                ),
                [["houses_lst", "rooms"]],
            )
        self.assertEqual(lst1, lst2)
        with self.assertNumQueries(3):
            lst2 = self.traverse_qs(
                Person.objects.prefetch_related(
                    Prefetch("houses", to_attr="houses_lst"),
                    Prefetch("houses_lst__rooms", to_attr="rooms_lst"),
                ),
                [["houses_lst", "rooms_lst"]],
            )
        self.assertEqual(lst1, lst2)