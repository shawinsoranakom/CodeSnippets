def test_union(self):
        """Union with all combinations of geometries/geometry fields."""
        geom = Point(-95.363151, 29.763374, srid=4326)

        union = (
            City.objects.annotate(union=functions.Union("point", geom))
            .get(name="Dallas")
            .union
        )
        expected = fromstr(
            "MULTIPOINT(-96.801611 32.782057,-95.363151 29.763374)", srid=4326
        )
        self.assertTrue(expected.equals(union))

        union = (
            City.objects.annotate(union=functions.Union(geom, "point"))
            .get(name="Dallas")
            .union
        )
        self.assertTrue(expected.equals(union))

        union = (
            City.objects.annotate(union=functions.Union("point", "point"))
            .get(name="Dallas")
            .union
        )
        expected = GEOSGeometry("POINT(-96.801611 32.782057)", srid=4326)
        self.assertTrue(expected.equals(union))

        union = (
            City.objects.annotate(union=functions.Union(geom, geom))
            .get(name="Dallas")
            .union
        )
        self.assertTrue(geom.equals(union))