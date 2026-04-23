def test_country(self):
        g = GeoIP2(city="<invalid>")
        self.assertIs(g.is_city, False)
        self.assertIs(g.is_country, True)
        for query in self.query_values:
            with self.subTest(query=query):
                self.assertEqual(g.country(query), self.expected_country)
                self.assertEqual(
                    g.country_code(query), self.expected_country["country_code"]
                )
                self.assertEqual(
                    g.country_name(query), self.expected_country["country_name"]
                )