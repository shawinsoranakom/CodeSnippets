def test_reverse_m2m(self):
        # Control lookups.
        with self.assertNumQueries(2):
            lst1 = self.traverse_qs(
                House.objects.prefetch_related("occupants"), [["occupants"]]
            )

        # Test lookups.
        with self.assertNumQueries(2):
            lst2 = self.traverse_qs(
                House.objects.prefetch_related(Prefetch("occupants")), [["occupants"]]
            )
        self.assertEqual(lst1, lst2)
        with self.assertNumQueries(2):
            lst2 = self.traverse_qs(
                House.objects.prefetch_related(
                    Prefetch("occupants", to_attr="occupants_lst")
                ),
                [["occupants_lst"]],
            )
        self.assertEqual(lst1, lst2)