def test_from_ewkt_empty_string(self):
        msg = "Expected WKT but got an empty string."
        with self.assertRaisesMessage(ValueError, msg):
            GEOSGeometry.from_ewkt("")
        with self.assertRaisesMessage(ValueError, msg):
            GEOSGeometry.from_ewkt("SRID=1;")