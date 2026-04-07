def test03_get_wkt(self):
        "Testing getting the WKT."
        for s in srlist:
            srs = SpatialReference(s.wkt)
            # GDAL 3 strips UNIT part in the last occurrence.
            self.assertEqual(
                s.wkt.replace(',UNIT["Meter",1]', ""),
                srs.wkt.replace(',UNIT["Meter",1]', ""),
            )