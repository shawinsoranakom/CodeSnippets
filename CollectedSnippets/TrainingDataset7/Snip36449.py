def test_parsing_asctime(self):
        parsed = parse_http_date("Sun Nov  6 08:49:37 1994")
        self.assertEqual(
            datetime.fromtimestamp(parsed, UTC),
            datetime(1994, 11, 6, 8, 49, 37, tzinfo=UTC),
        )