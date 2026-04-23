def test04_wkbwriter(self):
        wkb_w = WKBWriter()

        # Representations of 'POINT (5 23)' in hex -- one normal and
        # the other with the byte order changed.
        g = GEOSGeometry("POINT (5 23)")
        hex1 = b"010100000000000000000014400000000000003740"
        wkb1 = memoryview(binascii.a2b_hex(hex1))
        hex2 = b"000000000140140000000000004037000000000000"
        wkb2 = memoryview(binascii.a2b_hex(hex2))

        self.assertEqual(hex1, wkb_w.write_hex(g))
        self.assertEqual(wkb1, wkb_w.write(g))

        # Ensuring bad byteorders are not accepted.
        msg = "Byte order parameter must be 0 (Big Endian) or 1 (Little Endian)."
        for bad_byteorder in (-1, 2, 523, "foo", None):
            # Equivalent of `wkb_w.byteorder = bad_byteorder`
            with (
                self.subTest(bad_byteorder=bad_byteorder),
                self.assertRaisesMessage(ValueError, msg),
            ):
                wkb_w._set_byteorder(bad_byteorder)

        # Setting the byteorder to 0 (for Big Endian)
        wkb_w.byteorder = 0
        self.assertEqual(hex2, wkb_w.write_hex(g))
        self.assertEqual(wkb2, wkb_w.write(g))

        # Back to Little Endian
        wkb_w.byteorder = 1

        # Now, trying out the 3D and SRID flags.
        g = GEOSGeometry("POINT (5 23 17)")
        g.srid = 4326

        hex3d = b"0101000080000000000000144000000000000037400000000000003140"
        wkb3d = memoryview(binascii.a2b_hex(hex3d))
        hex3d_srid = (
            b"01010000A0E6100000000000000000144000000000000037400000000000003140"
        )
        wkb3d_srid = memoryview(binascii.a2b_hex(hex3d_srid))

        # Ensuring bad output dimensions are not accepted
        msg = "WKB output dimension must be 2 or 3"
        for bad_outdim in (-1, 0, 1, 4, 423, "foo", None):
            with (
                self.subTest(bad_outdim=bad_outdim),
                self.assertRaisesMessage(ValueError, msg),
            ):
                wkb_w.outdim = bad_outdim

        # Now setting the output dimensions to be 3
        wkb_w.outdim = 3

        self.assertEqual(hex3d, wkb_w.write_hex(g))
        self.assertEqual(wkb3d, wkb_w.write(g))

        # Telling the WKBWriter to include the srid in the representation.
        wkb_w.srid = True
        self.assertEqual(hex3d_srid, wkb_w.write_hex(g))
        self.assertEqual(wkb3d_srid, wkb_w.write(g))