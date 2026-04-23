def test_not_found(self):
        g1 = GeoIP2(city="<invalid>")
        g2 = GeoIP2(country="<invalid>")
        for function, query in itertools.product(
            (g1.country, g2.city), ("127.0.0.1", "::1")
        ):
            with self.subTest(function=function.__qualname__, query=query):
                msg = f"The address {query} is not in the database."
                with self.assertRaisesMessage(geoip2.errors.AddressNotFoundError, msg):
                    function(query)