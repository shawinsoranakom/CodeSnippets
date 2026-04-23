def test_distance_geodetic(self):
        """
        Test the `Distance` function on geodetic coordinate systems.
        """
        # Testing geodetic distance calculation with a non-point geometry
        # (a LineString of Wollongong and Shellharbour coords).
        ls = LineString(((150.902, -34.4245), (150.87, -34.5789)), srid=4326)

        # Reference query:
        #  SELECT ST_distance_sphere(
        #      point,
        #      ST_GeomFromText(
        #          'LINESTRING(150.9020 -34.4245,150.8700 -34.5789)',
        #          4326
        #      )
        #  )
        #  FROM distapp_australiacity ORDER BY name;
        distances = [
            1120954.92533513,
            140575.720018241,
            640396.662906304,
            60580.9693849269,
            972807.955955075,
            568451.8357838,
            40435.4335201384,
            0,
            68272.3896586844,
            12375.0643697706,
            0,
        ]
        qs = AustraliaCity.objects.annotate(distance=Distance("point", ls)).order_by(
            "name"
        )
        for city, distance in zip(qs, distances):
            with self.subTest(city=city, distance=distance):
                # Testing equivalence to within a meter (kilometer on
                # SpatiaLite).
                tol = -3 if connection.ops.spatialite else 0
                self.assertAlmostEqual(distance, city.distance.m, tol)