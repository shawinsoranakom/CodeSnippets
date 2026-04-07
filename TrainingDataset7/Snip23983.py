def test_length(self):
        """
        Test the `Length` function.
        """
        # Reference query (should use `length_spheroid`).
        #  SELECT ST_length_spheroid(
        #      ST_GeomFromText('<wkt>', 4326)
        #      'SPHEROID["WGS 84",6378137,298.257223563,
        #        AUTHORITY["EPSG","7030"]]'
        #  );
        len_m1 = 473504.769553813
        len_m2 = 4617.668

        if connection.features.supports_length_geodetic:
            qs = Interstate.objects.annotate(length=Length("path"))
            tol = 2 if connection.ops.oracle else 3
            self.assertAlmostEqual(len_m1, qs[0].length.m, tol)
            # TODO: test with spheroid argument (True and False)
        else:
            # Does not support geodetic coordinate systems.
            with self.assertRaises(NotSupportedError):
                list(Interstate.objects.annotate(length=Length("path")))

        # Now doing length on a projected coordinate system.
        i10 = SouthTexasInterstate.objects.annotate(length=Length("path")).get(
            name="I-10"
        )
        self.assertAlmostEqual(len_m2, i10.length.m, 2)
        self.assertTrue(
            SouthTexasInterstate.objects.annotate(length=Length("path"))
            .filter(length__gt=4000)
            .exists()
        )
        # Length with an explicit geometry value.
        qs = Interstate.objects.annotate(length=Length(i10.path))
        self.assertAlmostEqual(qs.first().length.m, len_m2, 2)