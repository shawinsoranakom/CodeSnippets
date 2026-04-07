def test_geodetic_distance_lookups(self):
        """
        Test distance lookups on geodetic coordinate systems.
        """
        # Line is from Canberra to Sydney. Query is for all other cities within
        # a 100km of that line (which should exclude only Hobart & # Adelaide).
        line = GEOSGeometry("LINESTRING(144.9630 -37.8143,151.2607 -33.8870)", 4326)
        dist_qs = AustraliaCity.objects.filter(point__distance_lte=(line, D(km=100)))
        expected_cities = [
            "Batemans Bay",
            "Canberra",
            "Hillsdale",
            "Melbourne",
            "Mittagong",
            "Shellharbour",
            "Sydney",
            "Thirroul",
            "Wollongong",
        ]
        if connection.ops.spatialite:
            # SpatiaLite is less accurate and returns 102.8km for Batemans Bay.
            expected_cities.pop(0)
        self.assertEqual(expected_cities, self.get_names(dist_qs))

        msg = "2, 3, or 4-element tuple required for 'distance_lte' lookup."
        with self.assertRaisesMessage(ValueError, msg):  # Too many params.
            len(
                AustraliaCity.objects.filter(
                    point__distance_lte=(
                        "POINT(5 23)",
                        D(km=100),
                        "spheroid",
                        "4",
                        None,
                    )
                )
            )

        with self.assertRaisesMessage(ValueError, msg):  # Too few params.
            len(AustraliaCity.objects.filter(point__distance_lte=("POINT(5 23)",)))

        msg = "For 4-element tuples the last argument must be the 'spheroid' directive."
        with self.assertRaisesMessage(ValueError, msg):
            len(
                AustraliaCity.objects.filter(
                    point__distance_lte=("POINT(5 23)", D(km=100), "spheroid", "4")
                )
            )

        # Getting all cities w/in 550 miles of Hobart.
        hobart = AustraliaCity.objects.get(name="Hobart")
        qs = AustraliaCity.objects.exclude(name="Hobart").filter(
            point__distance_lte=(hobart.point, D(mi=550))
        )
        cities = self.get_names(qs)
        self.assertEqual(cities, ["Batemans Bay", "Canberra", "Melbourne"])

        # Cities that are either really close or really far from Wollongong --
        # and using different units of distance.
        wollongong = AustraliaCity.objects.get(name="Wollongong")
        d1, d2 = D(yd=19500), D(nm=400)  # Yards (~17km) & Nautical miles.

        # Normal geodetic distance lookup (uses `distance_sphere` on PostGIS.
        gq1 = Q(point__distance_lte=(wollongong.point, d1))
        gq2 = Q(point__distance_gte=(wollongong.point, d2))
        qs1 = AustraliaCity.objects.exclude(name="Wollongong").filter(gq1 | gq2)

        # Geodetic distance lookup but telling GeoDjango to use
        # `distance_spheroid` instead (we should get the same results b/c
        # accuracy variance won't matter in this test case).
        querysets = [qs1]
        if connection.features.has_DistanceSpheroid_function:
            gq3 = Q(point__distance_lte=(wollongong.point, d1, "spheroid"))
            gq4 = Q(point__distance_gte=(wollongong.point, d2, "spheroid"))
            qs2 = AustraliaCity.objects.exclude(name="Wollongong").filter(gq3 | gq4)
            querysets.append(qs2)

        for qs in querysets:
            cities = self.get_names(qs)
            self.assertEqual(cities, ["Adelaide", "Hobart", "Shellharbour", "Thirroul"])