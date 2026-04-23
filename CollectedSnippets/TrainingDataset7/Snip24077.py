def test_curvepolygon_has_polygon_features(self):
        geom = OGRGeometry(
            "CURVEPOLYGON ZM (CIRCULARSTRING ZM (0 0 0 0, 4 0 0 0, 4 4 0 0, 0 4 0 0, "
            "0 0 0 0), (1 1 0 0, 3 3 0 0, 3 1 0 0, 1 1 0 0))"
        )
        self.assertIsInstance(geom, CurvePolygon)
        self.assertIsInstance(geom.shell, CircularString)