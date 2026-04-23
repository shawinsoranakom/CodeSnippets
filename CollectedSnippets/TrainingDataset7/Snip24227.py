def test_union_mixed_srid(self):
        """The result SRID depends on the order of parameters."""
        geom = Point(61.42915, 55.15402, srid=4326)
        geom_3857 = geom.transform(3857, clone=True)
        tol = 0.001

        for city in City.objects.annotate(union=functions.Union("point", geom_3857)):
            expected = city.point | geom
            self.assertTrue(city.union.equals_exact(expected, tol))
            self.assertEqual(city.union.srid, 4326)

        for city in City.objects.annotate(union=functions.Union(geom_3857, "point")):
            expected = geom_3857 | city.point.transform(3857, clone=True)
            self.assertTrue(expected.equals_exact(city.union, tol))
            self.assertEqual(city.union.srid, 3857)