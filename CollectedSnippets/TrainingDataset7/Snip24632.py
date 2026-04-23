def test_init(self):
        # Everything inferred from GeoIP path.
        g1 = GeoIP2()
        # Path passed explicitly.
        g2 = GeoIP2(settings.GEOIP_PATH, GeoIP2.MODE_AUTO)
        # Path provided as a string.
        g3 = GeoIP2(str(settings.GEOIP_PATH))
        # Only passing in the location of one database.
        g4 = GeoIP2(settings.GEOIP_PATH / settings.GEOIP_CITY, country="")
        g5 = GeoIP2(settings.GEOIP_PATH / settings.GEOIP_COUNTRY, city="")
        for g in (g1, g2, g3, g4, g5):
            self.assertTrue(g._reader)

        # Improper parameters.
        bad_params = (23, "foo", 15.23)
        for bad in bad_params:
            with self.assertRaises(GeoIP2Exception):
                GeoIP2(cache=bad)
            if isinstance(bad, str):
                e = GeoIP2Exception
            else:
                e = TypeError
            with self.assertRaises(e):
                GeoIP2(bad, GeoIP2.MODE_AUTO)