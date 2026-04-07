def test_list_with_select_related(self):
        """select_related() applies to entire lists, not just items."""
        with self.assertNumQueries(1):
            world = Species.objects.select_related()
            families = [o.genus.family.name for o in world]
            self.assertEqual(
                sorted(families),
                [
                    "Amanitacae",
                    "Drosophilidae",
                    "Fabaceae",
                    "Hominidae",
                ],
            )