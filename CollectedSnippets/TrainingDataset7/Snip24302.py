def test_distance_function(self):
        """
        Testing Distance() support on non-point geography fields.
        """
        if connection.ops.oracle:
            ref_dists = [0, 4899.68, 8081.30, 9115.15]
        elif connection.ops.spatialite:
            if connection.ops.spatial_version < (5,):
                # SpatiaLite < 5 returns non-zero distance for polygons and
                # points covered by that polygon.
                ref_dists = [326.61, 4899.68, 8081.30, 9115.15]
            else:
                ref_dists = [0, 4899.68, 8081.30, 9115.15]
        else:
            ref_dists = [0, 4891.20, 8071.64, 9123.95]
        htown = City.objects.get(name="Houston")
        qs = Zipcode.objects.annotate(
            distance=Distance("poly", htown.point),
            distance2=Distance(htown.point, "poly"),
        )
        for z, ref in zip(qs, ref_dists):
            self.assertAlmostEqual(z.distance.m, ref, 2)

        if connection.ops.postgis:
            # PostGIS casts geography to geometry when distance2 is calculated.
            ref_dists = [0, 4899.68, 8081.30, 9115.15]
        for z, ref in zip(qs, ref_dists):
            self.assertAlmostEqual(z.distance2.m, ref, 2)

        if not connection.ops.spatialite:
            # Distance function combined with a lookup.
            hzip = Zipcode.objects.get(code="77002")
            self.assertEqual(qs.get(distance__lte=0), hzip)