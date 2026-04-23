def test_traverse_multiple_items_property(self):
        # Control lookups.
        with self.assertNumQueries(4):
            lst1 = self.traverse_qs(
                Person.objects.prefetch_related(
                    "houses",
                    "all_houses__occupants__houses",
                ),
                [["all_houses", "occupants", "houses"]],
            )

        # Test lookups.
        with self.assertNumQueries(4):
            lst2 = self.traverse_qs(
                Person.objects.prefetch_related(
                    "houses",
                    Prefetch("all_houses__occupants", to_attr="occupants_lst"),
                    "all_houses__occupants_lst__houses",
                ),
                [["all_houses", "occupants_lst", "houses"]],
            )
        self.assertEqual(lst1, lst2)