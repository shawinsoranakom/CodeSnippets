def test_city(self):
        g = GeoIP2(country="<invalid>")
        self.assertIs(g.is_city, True)
        self.assertIs(g.is_country, False)
        for query in self.query_values:
            with self.subTest(query=query):
                self.assertEqual(g.city(query), self.expected_city)

                geom = g.geos(query)
                self.assertIsInstance(geom, GEOSGeometry)
                self.assertEqual(geom.srid, 4326)

                expected_lat = self.expected_city["latitude"]
                expected_lon = self.expected_city["longitude"]
                self.assertEqual(geom.tuple, (expected_lon, expected_lat))
                self.assertEqual(g.lat_lon(query), (expected_lat, expected_lon))
                self.assertEqual(g.lon_lat(query), (expected_lon, expected_lat))

                # Country queries should still work.
                self.assertEqual(g.country(query), self.expected_country)
                self.assertEqual(
                    g.country_code(query), self.expected_country["country_code"]
                )
                self.assertEqual(
                    g.country_name(query), self.expected_country["country_name"]
                )