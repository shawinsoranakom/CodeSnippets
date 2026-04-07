def test_country_using_city_database(self):
        g = GeoIP2(country="<invalid>")
        self.assertIs(g.is_city, True)
        self.assertIs(g.is_country, False)
        for query in self.query_values:
            with self.subTest(query=query):
                self.assertEqual(g.country(query), self.expected_country)
                self.assertEqual(
                    g.country_code(query), self.expected_country["country_code"]
                )
                self.assertEqual(
                    g.country_name(query), self.expected_country["country_name"]
                )