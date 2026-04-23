def test03_wkbreader(self):
        # Creating a WKBReader instance
        wkb_r = WKBReader()

        hex_bin = b"000000000140140000000000004037000000000000"
        hex_str = "000000000140140000000000004037000000000000"
        wkb = memoryview(binascii.a2b_hex(hex_bin))
        ref = GEOSGeometry(hex_bin)

        # read() should return a GEOSGeometry on either a hex string or
        # a WKB buffer.
        g1 = wkb_r.read(wkb)
        g2 = wkb_r.read(hex_bin)
        g3 = wkb_r.read(hex_str)
        for geom in (g1, g2, g3):
            with self.subTest(geom=geom):
                self.assertEqual(ref, geom)

        bad_input = (1, 5.23, None, False)
        msg = "'wkb' must be bytes, str or memoryview (got {} instead)."
        for bad_wkb in bad_input:
            with (
                self.subTest(bad_wkb=bad_wkb),
                self.assertRaisesMessage(TypeError, msg.format(bad_wkb)),
            ):
                wkb_r.read(bad_wkb)