def test_hex(self):
        "Testing HEX input/output."
        for g in self.geometries.hex_wkt:
            geom1 = OGRGeometry(g.wkt)
            self.assertEqual(g.hex.encode(), geom1.hex)
            # Constructing w/HEX
            geom2 = OGRGeometry(g.hex)
            self.assertEqual(geom1, geom2)