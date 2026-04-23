def test_distance_geodetic_spheroid(self):
        tol = 2 if connection.ops.oracle else 4

        # Got the reference distances using the raw SQL statements:
        #  SELECT ST_distance_spheroid(
        #      point,
        #      ST_GeomFromText('POINT(151.231341 -33.952685)', 4326),
        #      'SPHEROID["WGS 84",6378137.0,298.257223563]'
        #  )
        #  FROM distapp_australiacity WHERE (NOT (id = 11));
        #  SELECT ST_distance_sphere(
        #      point,
        #      ST_GeomFromText('POINT(151.231341 -33.952685)', 4326)
        #  )
        #  FROM distapp_australiacity
        #  WHERE (NOT (id = 11));  st_distance_sphere
        spheroid_distances = [
            60504.0628957201,
            77023.9489850262,
            49154.8867574404,
            90847.4358768573,
            217402.811919332,
            709599.234564757,
            640011.483550888,
            7772.00667991925,
            1047861.78619339,
            1165126.55236034,
        ]
        sphere_distances = [
            60580.9693849267,
            77144.0435286473,
            49199.4415344719,
            90804.7533823494,
            217713.384600405,
            709134.127242793,
            639828.157159169,
            7786.82949717788,
            1049204.06569028,
            1162623.7238134,
        ]
        # Testing with spheroid distances first.
        hillsdale = AustraliaCity.objects.get(name="Hillsdale")
        qs = (
            AustraliaCity.objects.exclude(id=hillsdale.id)
            .annotate(distance=Distance("point", hillsdale.point, spheroid=True))
            .order_by("id")
        )
        for i, c in enumerate(qs):
            with self.subTest(c=c):
                self.assertAlmostEqual(spheroid_distances[i], c.distance.m, tol)
        if connection.ops.postgis or connection.ops.spatialite:
            # PostGIS uses sphere-only distances by default, testing these as
            # well.
            qs = (
                AustraliaCity.objects.exclude(id=hillsdale.id)
                .annotate(distance=Distance("point", hillsdale.point))
                .order_by("id")
            )
            for i, c in enumerate(qs):
                with self.subTest(c=c):
                    self.assertAlmostEqual(sphere_distances[i], c.distance.m, tol)