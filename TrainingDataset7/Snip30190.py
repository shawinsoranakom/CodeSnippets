def test_m2m_through_fk(self):
        # Control lookups.
        with self.assertNumQueries(3):
            lst1 = self.traverse_qs(
                Room.objects.prefetch_related("house__occupants"),
                [["house", "occupants"]],
            )

        # Test lookups.
        with self.assertNumQueries(3):
            lst2 = self.traverse_qs(
                Room.objects.prefetch_related(Prefetch("house__occupants")),
                [["house", "occupants"]],
            )
        self.assertEqual(lst1, lst2)
        with self.assertNumQueries(3):
            lst2 = self.traverse_qs(
                Room.objects.prefetch_related(
                    Prefetch("house__occupants", to_attr="occupants_lst")
                ),
                [["house", "occupants_lst"]],
            )
        self.assertEqual(lst1, lst2)