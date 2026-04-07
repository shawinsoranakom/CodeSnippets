def test_list_without_select_related(self):
        with self.assertNumQueries(9):
            world = Species.objects.all()
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