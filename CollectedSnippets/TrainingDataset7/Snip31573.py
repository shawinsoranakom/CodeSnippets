def test_certain_fields(self):
        """
        The optional fields passed to select_related() control which related
        models we pull in. This allows for smaller queries.

        In this case, we explicitly say to select the 'genus' and
        'genus.family' models, leading to the same number of queries as before.
        """
        with self.assertNumQueries(1):
            world = Species.objects.select_related("genus__family")
            families = [o.genus.family.name for o in world]
            self.assertEqual(
                sorted(families),
                ["Amanitacae", "Drosophilidae", "Fabaceae", "Hominidae"],
            )