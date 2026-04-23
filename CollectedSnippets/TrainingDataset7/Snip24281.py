def test_relate_lookup(self):
        "Testing the 'relate' lookup type."
        # To make things more interesting, we will have our Texas reference
        # point in different SRIDs.
        pnt1 = fromstr("POINT (649287.0363174 4177429.4494686)", srid=2847)
        pnt2 = fromstr("POINT(-98.4919715741052 29.4333344025053)", srid=4326)

        # Not passing in a geometry as first param raises a TypeError when
        # initializing the QuerySet.
        with self.assertRaises(ValueError):
            Country.objects.filter(mpoly__relate=(23, "foo"))

        # Making sure the right exception is raised for the given
        # bad arguments.
        for bad_args, e in [
            ((pnt1, 0), ValueError),
            ((pnt2, "T*T***FF*", 0), ValueError),
        ]:
            qs = Country.objects.filter(mpoly__relate=bad_args)
            with self.assertRaises(e):
                qs.count()

        contains_mask = "T*T***FF*"
        within_mask = "T*F**F***"
        intersects_mask = "T********"
        # Relate works differently on Oracle.
        if connection.ops.oracle:
            contains_mask = "contains"
            within_mask = "inside"
            # TODO: This is not quite the same as the PostGIS mask above
            intersects_mask = "overlapbdyintersect"

        # Testing contains relation mask.
        if connection.features.supports_transform:
            self.assertEqual(
                Country.objects.get(mpoly__relate=(pnt1, contains_mask)).name,
                "Texas",
            )
        self.assertEqual(
            "Texas", Country.objects.get(mpoly__relate=(pnt2, contains_mask)).name
        )

        # Testing within relation mask.
        ks = State.objects.get(name="Kansas")
        self.assertEqual(
            "Lawrence",
            # Remove ".filter(name="Lawrence")" once PostGIS 3.5.4 is released.
            # https://lists.osgeo.org/pipermail/postgis-devel/2025-July/030581.html
            City.objects.filter(name="Lawrence")
            .get(point__relate=(ks.poly, within_mask))
            .name,
        )

        # Testing intersection relation mask.
        if not connection.ops.oracle:
            if connection.features.supports_transform:
                self.assertEqual(
                    Country.objects.get(mpoly__relate=(pnt1, intersects_mask)).name,
                    "Texas",
                )
            self.assertEqual(
                "Texas", Country.objects.get(mpoly__relate=(pnt2, intersects_mask)).name
            )
            self.assertEqual(
                "Lawrence",
                City.objects.get(point__relate=(ks.poly, intersects_mask)).name,
            )

        # With a complex geometry expression
        mask = "anyinteract" if connection.ops.oracle else within_mask
        self.assertFalse(
            City.objects.exclude(
                point__relate=(functions.Union("point", "point"), mask)
            )
        )