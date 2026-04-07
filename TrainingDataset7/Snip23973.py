def test_distance_projected(self):
        """
        Test the `Distance` function on projected coordinate systems.
        """
        # The point for La Grange, TX
        lagrange = GEOSGeometry("POINT(-96.876369 29.905320)", 4326)
        # Reference distances in feet and in meters. Got these values from
        # using the provided raw SQL statements.
        #  SELECT ST_Distance(
        #      point,
        #      ST_Transform(
        #          ST_GeomFromText('POINT(-96.876369 29.905320)', 4326),
        #          32140
        #      )
        #  )
        #  FROM distapp_southtexascity;
        m_distances = [
            147075.069813,
            139630.198056,
            140888.552826,
            138809.684197,
            158309.246259,
            212183.594374,
            70870.188967,
            165337.758878,
            139196.085105,
        ]
        #  SELECT ST_Distance(
        #      point,
        #      ST_Transform(
        #          ST_GeomFromText('POINT(-96.876369 29.905320)', 4326),
        #          2278
        #      )
        #  )
        #  FROM distapp_southtexascityft;
        ft_distances = [
            482528.79154625,
            458103.408123001,
            462231.860397575,
            455411.438904354,
            519386.252102563,
            696139.009211594,
            232513.278304279,
            542445.630586414,
            456679.155883207,
        ]

        # Testing using different variations of parameters and using models
        # with different projected coordinate systems.
        dist1 = SouthTexasCity.objects.annotate(
            distance=Distance("point", lagrange)
        ).order_by("id")
        dist2 = SouthTexasCityFt.objects.annotate(
            distance=Distance("point", lagrange)
        ).order_by("id")
        dist_qs = [dist1, dist2]

        # Ensuring expected distances are returned for each distance queryset.
        for qs in dist_qs:
            for i, c in enumerate(qs):
                with self.subTest(c=c):
                    self.assertAlmostEqual(m_distances[i], c.distance.m, -1)
                    self.assertAlmostEqual(ft_distances[i], c.distance.survey_ft, -1)