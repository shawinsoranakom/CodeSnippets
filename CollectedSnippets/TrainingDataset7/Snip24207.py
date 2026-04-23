def test_closest_point(self):
        qs = Country.objects.annotate(
            closest_point=functions.ClosestPoint("mpoly", functions.Centroid("mpoly"))
        )
        for country in qs:
            self.assertIsInstance(country.closest_point, Point)
            self.assertEqual(
                country.mpoly.intersection(country.closest_point),
                country.closest_point,
            )