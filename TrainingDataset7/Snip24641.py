def test_missing_path(self):
        msg = "GeoIP path must be provided via parameter or the GEOIP_PATH setting."
        with self.settings(GEOIP_PATH=None):
            with self.assertRaisesMessage(GeoIP2Exception, msg):
                GeoIP2()