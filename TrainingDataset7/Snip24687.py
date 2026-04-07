def test_srs_with_invalid_wkt_and_proj4(self):
        class MockSpatialRefSys(SpatialRefSysMixin):
            def __init__(self, wkt=None, proj4text=None):
                self.wkt = wkt
                self.proj4text = proj4text

        with self.assertRaisesMessage(
            Exception,
            "Could not get OSR SpatialReference.\n"
            "Error for WKT 'INVALID_WKT': Corrupt data.\n"
            "Error for PROJ.4 '+proj=invalid': Corrupt data.",
        ):
            MockSpatialRefSys(wkt="INVALID_WKT", proj4text="+proj=invalid").srs