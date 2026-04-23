def test_fromfile(self):
        "Testing the fromfile() factory."
        ref_pnt = GEOSGeometry("POINT(5 23)")

        wkt_f = BytesIO()
        wkt_f.write(ref_pnt.wkt.encode())
        wkb_f = BytesIO()
        wkb_f.write(bytes(ref_pnt.wkb))

        # Other tests use `fromfile()` on string filenames so those
        # aren't tested here.
        for fh in (wkt_f, wkb_f):
            fh.seek(0)
            pnt = fromfile(fh)
            with self.subTest(fh=fh):
                self.assertEqual(ref_pnt, pnt)