def test_parsing(self):
        self.assertEqual(
            parse_etags(r'"" ,  "etag", "e\\tag", W/"weak"'),
            ['""', '"etag"', r'"e\\tag"', 'W/"weak"'],
        )
        self.assertEqual(parse_etags("*"), ["*"])

        # Ignore RFC 2616 ETags that are invalid according to RFC 9110.
        self.assertEqual(parse_etags(r'"etag", "e\"t\"ag"'), ['"etag"'])