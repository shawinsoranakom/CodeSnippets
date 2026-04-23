def test_bad_query(self):
        g = GeoIP2(city="<invalid>")

        functions = (g.city, g.geos, g.lat_lon, g.lon_lat)
        msg = "Invalid GeoIP city data file: "
        for function in functions:
            with self.subTest(function=function.__qualname__):
                with self.assertRaisesMessage(GeoIP2Exception, msg):
                    function("example.com")

        functions += (g.country, g.country_code, g.country_name)
        values = (123, 123.45, b"", (), [], {}, set(), frozenset(), GeoIP2)
        msg = (
            "GeoIP query must be a string or instance of IPv4Address or IPv6Address, "
            "not type"
        )
        for function, value in itertools.product(functions, values):
            with self.subTest(function=function.__qualname__, type=type(value)):
                with self.assertRaisesMessage(TypeError, msg):
                    function(value)