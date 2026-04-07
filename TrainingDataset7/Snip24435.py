def test_empty_polygon_wkb(self):
        p = Polygon(srid=4326)
        p_no_srid = Polygon()
        wkb_w = WKBWriter()
        wkb_w.srid = True
        for byteorder, hexes in enumerate(
            [
                (b"000000000300000000", b"0020000003000010E600000000"),
                (b"010300000000000000", b"0103000020E610000000000000"),
            ]
        ):
            wkb_w.byteorder = byteorder
            for srid, hex in enumerate(hexes):
                wkb_w.srid = srid
                with self.subTest(byteorder=byteorder, hexes=hexes):
                    self.assertEqual(wkb_w.write_hex(p), hex)
                    self.assertEqual(
                        GEOSGeometry(wkb_w.write_hex(p)), p if srid else p_no_srid
                    )
                    self.assertEqual(wkb_w.write(p), memoryview(binascii.a2b_hex(hex)))
                    self.assertEqual(
                        GEOSGeometry(wkb_w.write(p)), p if srid else p_no_srid
                    )