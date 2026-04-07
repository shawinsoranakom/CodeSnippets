def test01_wktreader(self):
        # Creating a WKTReader instance
        wkt_r = WKTReader()
        wkt = "POINT (5 23)"

        # read() should return a GEOSGeometry
        ref = GEOSGeometry(wkt)
        g1 = wkt_r.read(wkt.encode())
        g2 = wkt_r.read(wkt)

        for geom in (g1, g2):
            with self.subTest(geom=geom):
                self.assertEqual(ref, geom)

        # Should only accept string objects.
        bad_input = (1, 5.23, None, False, memoryview(b"foo"))
        msg = "'wkt' must be bytes or str (got {} instead)."
        for bad_wkt in bad_input:
            with (
                self.subTest(bad_wkt=bad_wkt),
                self.assertRaisesMessage(TypeError, msg.format(bad_wkt)),
            ):
                wkt_r.read(bad_wkt)