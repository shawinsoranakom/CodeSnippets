def test_hex(self):
        "Testing HEX output."
        for g in self.geometries.hex_wkt:
            with self.subTest(g=g):
                geom = fromstr(g.wkt)
                self.assertEqual(g.hex, geom.hex.decode())