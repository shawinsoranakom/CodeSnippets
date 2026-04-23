def test_hexewkb(self):
        "Testing (HEX)EWKB output."
        # For testing HEX(EWKB).
        ogc_hex = b"01010000000000000000000000000000000000F03F"
        ogc_hex_3d = b"01010000800000000000000000000000000000F03F0000000000000040"
        # `SELECT ST_AsHEXEWKB(ST_GeomFromText('POINT(0 1)', 4326));`
        hexewkb_2d = b"0101000020E61000000000000000000000000000000000F03F"
        # `SELECT ST_AsHEXEWKB(ST_GeomFromEWKT('SRID=4326;POINT(0 1 2)'));`
        hexewkb_3d = (
            b"01010000A0E61000000000000000000000000000000000F03F0000000000000040"
        )

        pnt_2d = Point(0, 1, srid=4326)
        pnt_3d = Point(0, 1, 2, srid=4326)

        # OGC-compliant HEX will not have SRID value.
        self.assertEqual(ogc_hex, pnt_2d.hex)
        self.assertEqual(ogc_hex_3d, pnt_3d.hex)

        # HEXEWKB should be appropriate for its dimension -- have to use an
        # a WKBWriter w/dimension set accordingly, else GEOS will insert
        # garbage into 3D coordinate if there is none.
        self.assertEqual(hexewkb_2d, pnt_2d.hexewkb)
        self.assertEqual(hexewkb_3d, pnt_3d.hexewkb)
        self.assertIs(GEOSGeometry(hexewkb_3d).hasz, True)

        # Same for EWKB.
        self.assertEqual(memoryview(a2b_hex(hexewkb_2d)), pnt_2d.ewkb)
        self.assertEqual(memoryview(a2b_hex(hexewkb_3d)), pnt_3d.ewkb)

        # Redundant sanity check.
        self.assertEqual(4326, GEOSGeometry(hexewkb_2d).srid)