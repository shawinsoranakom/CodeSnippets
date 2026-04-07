def test_wkt_invalid(self):
        msg = "String input unrecognized as WKT EWKT, and HEXEWKB."
        with self.assertRaisesMessage(ValueError, msg):
            fromstr("POINT(٠٠١ ٠)")
        with self.assertRaisesMessage(ValueError, msg):
            fromstr("SRID=٧٥٨٣;POINT(100 0)")