def test_parsing_year_less_than_70(self):
        parsed = parse_http_date("Sun Nov  6 08:49:37 0037")
        self.assertEqual(
            datetime.fromtimestamp(parsed, UTC),
            datetime(2037, 11, 6, 8, 49, 37, tzinfo=UTC),
        )