def test_distance_transform(self):
        """
        Test the `Distance` function used with `Transform` on a geographic
        field.
        """
        # We'll be using a Polygon (created by buffering the centroid
        # of 77005 to 100m) -- which aren't allowed in geographic distance
        # queries normally, however our field has been transformed to
        # a non-geographic system.
        z = SouthTexasZipcode.objects.get(name="77005")

        # Reference query:
        # SELECT ST_Distance(
        #   ST_Transform("distapp_censuszipcode"."poly", 32140),
        #   ST_GeomFromText('<buffer_wkt>', 32140))
        # FROM "distapp_censuszipcode";
        dists_m = [3553.30384972258, 1243.18391525602, 2186.15439472242]

        # Having our buffer in the SRID of the transformation and of the field
        # -- should get the same results. The first buffer has no need for
        # transformation SQL because it is the same SRID as what was given
        # to `transform()`. The second buffer will need to be transformed,
        # however.
        buf1 = z.poly.centroid.buffer(100)
        buf2 = buf1.transform(4269, clone=True)
        ref_zips = ["77002", "77025", "77401"]

        for buf in [buf1, buf2]:
            qs = (
                CensusZipcode.objects.exclude(name="77005")
                .annotate(distance=Distance(Transform("poly", 32140), buf))
                .order_by("name")
            )
            self.assertEqual(ref_zips, sorted(c.name for c in qs))
            for i, z in enumerate(qs):
                self.assertAlmostEqual(z.distance.m, dists_m[i], 5)