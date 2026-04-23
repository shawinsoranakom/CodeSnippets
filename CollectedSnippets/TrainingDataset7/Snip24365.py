def test_srid(self):
        "Testing the SRID property and keyword."
        # Testing SRID keyword on Point
        pnt = Point(5, 23, srid=4326)
        self.assertEqual(4326, pnt.srid)
        pnt.srid = 3084
        self.assertEqual(3084, pnt.srid)
        with self.assertArgumentTypeError(3, "str"):
            pnt.srid = "4326"

        # Testing SRID keyword on fromstr(), and on Polygon rings.
        poly = fromstr(self.geometries.polygons[1].wkt, srid=4269)
        self.assertEqual(4269, poly.srid)
        for ring in poly:
            with self.subTest(ring=ring):
                self.assertEqual(4269, ring.srid)
        poly.srid = 4326
        self.assertEqual(4326, poly.shell.srid)

        # Testing SRID keyword on GeometryCollection
        gc = GeometryCollection(
            Point(5, 23), LineString((0, 0), (1.5, 1.5), (3, 3)), srid=32021
        )
        self.assertEqual(32021, gc.srid)
        for geom in gc:
            with self.subTest(geom=geom):
                self.assertEqual(32021, geom.srid)

        # GEOS may get the SRID from HEXEWKB
        # 'POINT(5 23)' at SRID=4326 in hex form -- obtained from PostGIS
        # using `SELECT GeomFromText('POINT (5 23)', 4326);`.
        hex = "0101000020E610000000000000000014400000000000003740"
        p1 = fromstr(hex)
        self.assertEqual(4326, p1.srid)

        p2 = fromstr(p1.hex)
        self.assertIsNone(p2.srid)
        p3 = fromstr(p1.hex, srid=-1)  # -1 is intended.
        self.assertEqual(-1, p3.srid)

        # Testing that geometry SRID could be set to its own value
        pnt_wo_srid = Point(1, 1)
        pnt_wo_srid.srid = pnt_wo_srid.srid

        # Input geometries that have an SRID.
        self.assertEqual(GEOSGeometry(pnt.ewkt, srid=pnt.srid).srid, pnt.srid)
        self.assertEqual(GEOSGeometry(pnt.ewkb, srid=pnt.srid).srid, pnt.srid)
        with self.assertRaisesMessage(
            ValueError, "Input geometry already has SRID: %d." % pnt.srid
        ):
            GEOSGeometry(pnt.ewkt, srid=1)
        with self.assertRaisesMessage(
            ValueError, "Input geometry already has SRID: %d." % pnt.srid
        ):
            GEOSGeometry(pnt.ewkb, srid=1)