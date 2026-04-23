def test_distance_simple(self):
        """
        Test a simple distance query, with projected coordinates and without
        transformation.
        """
        lagrange = GEOSGeometry("POINT(805066.295722839 4231496.29461335)", 32140)
        houston = (
            SouthTexasCity.objects.annotate(dist=Distance("point", lagrange))
            .order_by("id")
            .first()
        )
        tol = 2 if connection.ops.oracle else 5
        self.assertAlmostEqual(houston.dist.m, 147075.069813, tol)