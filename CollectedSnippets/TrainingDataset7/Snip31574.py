def test_more_certain_fields(self):
        """
        In this case, we explicitly say to select the 'genus' and
        'genus.family' models, leading to the same number of queries as before.
        """
        with self.assertNumQueries(2):
            world = Species.objects.filter(genus__name="Amanita").select_related(
                "genus__family"
            )
            orders = [o.genus.family.order.name for o in world]
            self.assertEqual(orders, ["Agaricales"])