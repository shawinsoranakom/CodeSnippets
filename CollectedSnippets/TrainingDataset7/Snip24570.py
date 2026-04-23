def test_related_union_aggregate(self):
        "Testing the `Union` aggregate on related geographic models."
        # This combines the Extent and Union aggregates into one query
        aggs = City.objects.aggregate(Union("location__point"))

        # These are the points that are components of the aggregate geographic
        # union that is returned. Each point # corresponds to City PK.
        p1 = Point(-104.528056, 33.387222)
        p2 = Point(-97.516111, 33.058333)
        p3 = Point(-79.460734, 40.18476)
        p4 = Point(-96.801611, 32.782057)
        p5 = Point(-95.363151, 29.763374)

        # The second union aggregate is for a union
        # query that includes limiting information in the WHERE clause (in
        # other words a `.filter()` precedes the call to `.aggregate(Union()`).
        ref_u1 = MultiPoint(p1, p2, p4, p5, p3, srid=4326)
        ref_u2 = MultiPoint(p2, p3, srid=4326)

        u1 = City.objects.aggregate(Union("location__point"))["location__point__union"]
        u2 = City.objects.exclude(
            name__in=("Roswell", "Houston", "Dallas", "Fort Worth"),
        ).aggregate(Union("location__point"))["location__point__union"]
        u3 = aggs["location__point__union"]
        self.assertEqual(type(u1), MultiPoint)
        self.assertEqual(type(u3), MultiPoint)

        # Ordering of points in the result of the union is not defined and
        # implementation-dependent (DB backend, GEOS version).
        tests = [
            (u1, ref_u1),
            (u2, ref_u2),
            (u3, ref_u1),
        ]
        for union, ref in tests:
            for point, ref_point in zip(sorted(union), sorted(ref), strict=True):
                self.assertIs(point.equals_exact(ref_point, tolerance=6), True)