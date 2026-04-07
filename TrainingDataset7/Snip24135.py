def test_srid(self):
        """The srid property returns top-level authority code."""
        for s in srlist:
            if hasattr(s, "epsg"):
                srs = SpatialReference(s.wkt)
                self.assertEqual(srs.srid, s.epsg)