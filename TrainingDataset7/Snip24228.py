def test_argument_validation(self):
        with self.assertRaisesMessage(
            ValueError, "SRID is required for all geometries."
        ):
            City.objects.annotate(geo=functions.GeoFunc(Point(1, 1)))

        msg = "GeoFunc function requires a GeometryField in position 1, got CharField."
        with self.assertRaisesMessage(TypeError, msg):
            City.objects.annotate(geo=functions.GeoFunc("name"))

        msg = "GeoFunc function requires a geometric argument in position 1."
        with self.assertRaisesMessage(TypeError, msg):
            City.objects.annotate(union=functions.GeoFunc(1, "point")).get(
                name="Dallas"
            )