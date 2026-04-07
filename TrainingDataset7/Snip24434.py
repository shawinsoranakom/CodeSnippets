def test_empty_point_wkb(self):
        p = Point(srid=4326)
        wkb_w = WKBWriter()

        wkb_w.srid = False
        with self.assertRaisesMessage(
            ValueError, "Empty point is not representable in WKB."
        ):
            wkb_w.write(p)
        with self.assertRaisesMessage(
            ValueError, "Empty point is not representable in WKB."
        ):
            wkb_w.write_hex(p)

        wkb_w.srid = True
        for byteorder, hex in enumerate(
            [
                b"0020000001000010E67FF80000000000007FF8000000000000",
                b"0101000020E6100000000000000000F87F000000000000F87F",
            ]
        ):
            wkb_w.byteorder = byteorder
            self.assertEqual(wkb_w.write_hex(p), hex)
            self.assertEqual(GEOSGeometry(wkb_w.write_hex(p)), p)
            self.assertEqual(wkb_w.write(p), memoryview(binascii.a2b_hex(hex)))
            self.assertEqual(GEOSGeometry(wkb_w.write(p)), p)