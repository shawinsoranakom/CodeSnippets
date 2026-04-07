def test_unsupported_database(self):
        msg = "Unable to handle database edition: GeoLite2-ASN"
        with self.settings(GEOIP_PATH=build_geoip_path("GeoLite2-ASN-Test.mmdb")):
            with self.assertRaisesMessage(GeoIP2Exception, msg):
                GeoIP2()