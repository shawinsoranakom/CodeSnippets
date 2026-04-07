def test_uri_to_iri(self):
        cases = [
            (None, None),
            # Valid UTF-8 sequences are decoded.
            ("/%e2%89%Ab%E2%99%a5%E2%89%aB/", "/≫♥≫/"),
            ("/%E2%99%A5%E2%99%A5/?utf8=%E2%9C%93", "/♥♥/?utf8=✓"),
            ("/%41%5a%6B/", "/AZk/"),
            # Reserved and non-URL valid ASCII chars are not decoded.
            ("/%25%20%02%41%7b/", "/%25%20%02A%7b/"),
            # Broken UTF-8 sequences remain escaped.
            ("/%AAd%AAj%AAa%AAn%AAg%AAo%AA/", "/%AAd%AAj%AAa%AAn%AAg%AAo%AA/"),
            ("/%E2%99%A5%E2%E2%99%A5/", "/♥%E2♥/"),
            ("/%E2%99%A5%E2%99%E2%99%A5/", "/♥%E2%99♥/"),
            ("/%E2%E2%99%A5%E2%99%A5%99/", "/%E2♥♥%99/"),
            (
                "/%E2%99%A5%E2%99%A5/?utf8=%9C%93%E2%9C%93%9C%93",
                "/♥♥/?utf8=%9C%93✓%9C%93",
            ),
        ]

        for uri, iri in cases:
            with self.subTest(uri):
                self.assertEqual(uri_to_iri(uri), iri)

                # Test idempotency.
                self.assertEqual(uri_to_iri(uri_to_iri(uri)), iri)