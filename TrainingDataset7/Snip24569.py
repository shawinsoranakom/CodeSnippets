def test_related_extent_annotate(self):
        """
        Test annotation with Extent GeoAggregate.
        """
        cities = City.objects.annotate(
            points_extent=Extent("location__point")
        ).order_by("name")
        tol = 4
        self.assertAlmostEqual(
            cities[0].points_extent, (-97.516111, 33.058333, -97.516111, 33.058333), tol
        )