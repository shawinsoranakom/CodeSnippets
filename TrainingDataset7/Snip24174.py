def test_geography_value(self):
        p = Polygon(((1, 1), (1, 2), (2, 2), (2, 1), (1, 1)))
        area = (
            City.objects.annotate(
                a=functions.Area(Value(p, GeometryField(srid=4326, geography=True)))
            )
            .first()
            .a
        )
        self.assertAlmostEqual(area.sq_km, 12305.1, 0)