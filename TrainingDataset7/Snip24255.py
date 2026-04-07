def test_lookup_insert_transform(self):
        "Testing automatic transform for lookups and inserts."
        # San Antonio in 'WGS84' (SRID 4326)
        sa_4326 = "POINT (-98.493183 29.424170)"
        wgs_pnt = fromstr(sa_4326, srid=4326)  # Our reference point in WGS84
        # San Antonio in 'WGS 84 / Pseudo-Mercator' (SRID 3857)
        other_srid_pnt = wgs_pnt.transform(3857, clone=True)
        # Constructing & querying with a point from a different SRID. Oracle
        # `SDO_OVERLAPBDYINTERSECT` operates differently from
        # `ST_Intersects`, so contains is used instead.
        if connection.ops.oracle:
            tx = Country.objects.get(mpoly__contains=other_srid_pnt)
        else:
            tx = Country.objects.get(mpoly__intersects=other_srid_pnt)
        self.assertEqual("Texas", tx.name)

        # Creating San Antonio. Remember the Alamo.
        sa = City.objects.create(name="San Antonio", point=other_srid_pnt)

        # Now verifying that San Antonio was transformed correctly
        sa = City.objects.get(name="San Antonio")
        self.assertAlmostEqual(wgs_pnt.x, sa.point.x, 6)
        self.assertAlmostEqual(wgs_pnt.y, sa.point.y, 6)

        # If the GeometryField SRID is -1, then we shouldn't perform any
        # transformation if the SRID of the input geometry is different.
        m1 = MinusOneSRID(geom=Point(17, 23, srid=4326))
        m1.save()
        self.assertEqual(-1, m1.geom.srid)