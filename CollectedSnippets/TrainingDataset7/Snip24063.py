def test_point_m_wkt_wkb(self):
        wkt = "POINT ZM (1 2 3 4)"
        geom = OGRGeometry(wkt)
        self.assertEqual(geom.wkt, wkt)
        self.assertEqual(
            geom.wkb.hex(),
            "01b90b0000000000000000f03f00000000000000"
            "4000000000000008400000000000001040",
        )
        wkt = "POINT M (1 2 3)"
        geom = OGRGeometry(wkt)
        self.assertEqual(geom.wkt, wkt)
        self.assertEqual(
            geom.wkb.hex(),
            "01d1070000000000000000f03f00000000000000400000000000000840",
        )