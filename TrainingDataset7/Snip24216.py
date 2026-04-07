def test_point_on_surface(self):
        qs = Country.objects.annotate(
            point_on_surface=functions.PointOnSurface("mpoly")
        )
        for country in qs:
            self.assertTrue(country.mpoly.intersection(country.point_on_surface))