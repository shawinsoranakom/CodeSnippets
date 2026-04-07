def test_has_curve(self):
        for geom in self.geometries.curved_geoms:
            with self.subTest(wkt=geom.wkt):
                geom = OGRGeometry(geom.wkt)
                self.assertIs(geom.has_curve, True)
                msg = f"GEOS does not support {geom.__class__.__qualname__}."
                with self.assertRaisesMessage(GEOSException, msg):
                    geom.geos
        geom = OGRGeometry("POINT (0 1)")
        self.assertIs(geom.has_curve, False)