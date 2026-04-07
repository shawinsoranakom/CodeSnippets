def test05_epsg(self):
        "Test EPSG import."
        for s in srlist:
            if s.epsg:
                srs1 = SpatialReference(s.wkt)
                srs2 = SpatialReference(s.epsg)
                srs3 = SpatialReference(str(s.epsg))
                srs4 = SpatialReference("EPSG:%d" % s.epsg)
                for srs in (srs1, srs2, srs3, srs4):
                    for attr, expected in s.attr:
                        self.assertEqual(expected, srs[attr])