def test_gml(self):
        "Testing GML output."
        for g in self.geometries.wkt_out:
            geom = OGRGeometry(g.wkt)
            exp_gml = g.gml
            self.assertEqual(exp_gml, geom.gml)