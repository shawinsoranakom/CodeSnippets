def test_snap_to_grid(self):
        # Let's try and break snap_to_grid() with bad combinations of
        # arguments.
        for bad_args in ((), range(3), range(5)):
            with self.assertRaises(ValueError):
                Country.objects.annotate(snap=functions.SnapToGrid("mpoly", *bad_args))
        for bad_args in (("1.0",), (1.0, None), tuple(map(str, range(4)))):
            with self.assertRaises(TypeError):
                Country.objects.annotate(snap=functions.SnapToGrid("mpoly", *bad_args))

        # Boundary for San Marino, courtesy of Bjorn Sandvik of
        # thematicmapping.org from the world borders dataset he provides.
        wkt = (
            "MULTIPOLYGON(((12.41580 43.95795,12.45055 43.97972,12.45389 43.98167,"
            "12.46250 43.98472,12.47167 43.98694,12.49278 43.98917,"
            "12.50555 43.98861,12.51000 43.98694,12.51028 43.98277,"
            "12.51167 43.94333,12.51056 43.93916,12.49639 43.92333,"
            "12.49500 43.91472,12.48778 43.90583,12.47444 43.89722,"
            "12.46472 43.89555,12.45917 43.89611,12.41639 43.90472,"
            "12.41222 43.90610,12.40782 43.91366,12.40389 43.92667,"
            "12.40500 43.94833,12.40889 43.95499,12.41580 43.95795)))"
        )
        Country.objects.create(name="San Marino", mpoly=fromstr(wkt))

        # Because floating-point arithmetic isn't exact, we set a tolerance
        # to pass into GEOS `equals_exact`.
        tol = 0.000000001

        # SELECT AsText(ST_SnapToGrid("geoapp_country"."mpoly", 0.1))
        # FROM "geoapp_country"
        # WHERE "geoapp_country"."name" = 'San Marino';
        ref = fromstr("MULTIPOLYGON(((12.4 44,12.5 44,12.5 43.9,12.4 43.9,12.4 44)))")
        self.assertTrue(
            ref.equals_exact(
                Country.objects.annotate(snap=functions.SnapToGrid("mpoly", 0.1))
                .get(name="San Marino")
                .snap,
                tol,
            )
        )

        # SELECT AsText(ST_SnapToGrid("geoapp_country"."mpoly", 0.05, 0.23))
        # FROM "geoapp_country"
        # WHERE "geoapp_country"."name" = 'San Marino';
        ref = fromstr(
            "MULTIPOLYGON(((12.4 43.93,12.45 43.93,12.5 43.93,12.45 43.93,12.4 43.93)))"
        )
        self.assertTrue(
            ref.equals_exact(
                Country.objects.annotate(snap=functions.SnapToGrid("mpoly", 0.05, 0.23))
                .get(name="San Marino")
                .snap,
                tol,
            )
        )

        # SELECT AsText(
        #     ST_SnapToGrid("geoapp_country"."mpoly", 0.5, 0.17, 0.05, 0.23))
        # FROM "geoapp_country"
        # WHERE "geoapp_country"."name" = 'San Marino';
        ref = fromstr(
            "MULTIPOLYGON(((12.4 43.87,12.45 43.87,12.45 44.1,12.5 44.1,12.5 43.87,"
            "12.45 43.87,12.4 43.87)))"
        )
        self.assertTrue(
            ref.equals_exact(
                Country.objects.annotate(
                    snap=functions.SnapToGrid("mpoly", 0.05, 0.23, 0.5, 0.17)
                )
                .get(name="San Marino")
                .snap,
                tol,
            )
        )