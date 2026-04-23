def test_diff_intersection_union(self):
        geom = Point(5, 23, srid=4326)
        qs = Country.objects.annotate(
            difference=functions.Difference("mpoly", geom),
            sym_difference=functions.SymDifference("mpoly", geom),
            union=functions.Union("mpoly", geom),
            intersection=functions.Intersection("mpoly", geom),
        )

        if connection.ops.oracle:
            # Should be able to execute the queries; however, they won't be the
            # same as GEOS (because Oracle doesn't use GEOS internally like
            # PostGIS or SpatiaLite).
            return
        for c in qs:
            self.assertTrue(c.mpoly.difference(geom).equals(c.difference))
            if connection.features.empty_intersection_returns_none:
                self.assertIsNone(c.intersection)
            else:
                self.assertIs(c.intersection.empty, True)
            self.assertTrue(c.mpoly.sym_difference(geom).equals(c.sym_difference))
            self.assertTrue(c.mpoly.union(geom).equals(c.union))