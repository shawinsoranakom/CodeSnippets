def test_geometry_distance(self):
        point = Point(-90, 40, srid=4326)
        qs = City.objects.annotate(
            distance=functions.GeometryDistance("point", point)
        ).order_by("distance")
        distances = (
            2.99091995527296,
            5.33507274054713,
            9.33852187483721,
            9.91769193646233,
            11.556465744884,
            14.713098433352,
            34.3635252198568,
            276.987855073372,
        )
        for city, expected_distance in zip(qs, distances):
            with self.subTest(city=city):
                self.assertAlmostEqual(city.distance, expected_distance)