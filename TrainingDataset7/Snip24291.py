def test_within_subquery(self):
        """
        Using a queryset inside a geo lookup is working (using a subquery)
        (#14483).
        """
        tex_cities = City.objects.filter(
            point__within=Country.objects.filter(name="Texas").values("mpoly")
        ).order_by("name")
        self.assertEqual(
            list(tex_cities.values_list("name", flat=True)), ["Dallas", "Houston"]
        )