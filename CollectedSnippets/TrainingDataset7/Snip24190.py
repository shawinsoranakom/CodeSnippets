def test_azimuth(self):
        # Returns the azimuth in radians.
        azimuth_expr = functions.Azimuth(Point(0, 0, srid=4326), Point(1, 1, srid=4326))
        self.assertAlmostEqual(
            City.objects.annotate(azimuth=azimuth_expr).first().azimuth,
            math.pi / 4,
            places=2,
        )
        # Returns None if the two points are coincident.
        azimuth_expr = functions.Azimuth(Point(0, 0, srid=4326), Point(0, 0, srid=4326))
        self.assertIsNone(City.objects.annotate(azimuth=azimuth_expr).first().azimuth)