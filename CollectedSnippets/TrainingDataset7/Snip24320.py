def test_kml(self):
        "Testing KML output."
        for tg in self.geometries.wkt_out:
            geom = fromstr(tg.wkt)
            kml = getattr(tg, "kml", False)
            if kml:
                with self.subTest(tg=tg):
                    self.assertEqual(kml, geom.kml)