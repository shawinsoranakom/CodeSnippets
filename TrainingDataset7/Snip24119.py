def test01_wkt(self):
        "Testing initialization on valid OGC WKT."
        for s in srlist:
            SpatialReference(s.wkt)