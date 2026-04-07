def test_from_ewkt_invalid_srid(self):
        msg = "EWKT has invalid SRID part."
        with self.assertRaisesMessage(ValueError, msg):
            GEOSGeometry.from_ewkt("SRUD=1;POINT(1 1)")
        with self.assertRaisesMessage(ValueError, msg):
            GEOSGeometry.from_ewkt("SRID=WGS84;POINT(1 1)")