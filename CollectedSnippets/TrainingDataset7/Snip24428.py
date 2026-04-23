def test02_wktwriter(self):
        # Creating a WKTWriter instance, testing its ptr property.
        wkt_w = WKTWriter()
        msg = "Incompatible pointer type: "
        with self.assertRaisesMessage(TypeError, msg):
            wkt_w.ptr = WKTReader.ptr_type()

        ref = GEOSGeometry("POINT (5 23)")
        ref_wkt = "POINT (5.0000000000000000 23.0000000000000000)"
        self.assertEqual(ref_wkt, wkt_w.write(ref).decode())