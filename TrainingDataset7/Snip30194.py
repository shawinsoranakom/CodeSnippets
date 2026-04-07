def test_traverse_single_item_property(self):
        # Control lookups.
        with self.assertNumQueries(5):
            lst1 = self.traverse_qs(
                Person.objects.prefetch_related(
                    "houses__rooms",
                    "primary_house__occupants__houses",
                ),
                [["primary_house", "occupants", "houses"]],
            )

        # Test lookups.
        with self.assertNumQueries(5):
            lst2 = self.traverse_qs(
                Person.objects.prefetch_related(
                    "houses__rooms",
                    Prefetch("primary_house__occupants", to_attr="occupants_lst"),
                    "primary_house__occupants_lst__houses",
                ),
                [["primary_house", "occupants_lst", "houses"]],
            )
        self.assertEqual(lst1, lst2)