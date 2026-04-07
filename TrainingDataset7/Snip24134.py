def test_esri(self):
        srs = SpatialReference("NAD83")
        pre_esri_wkt = srs.wkt
        srs.to_esri()
        self.assertNotEqual(srs.wkt, pre_esri_wkt)
        self.assertIn('DATUM["D_North_American_1983"', srs.wkt)
        srs.from_esri()
        self.assertIn('DATUM["North_American_Datum_1983"', srs.wkt)