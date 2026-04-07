def test_complementarity(self):
        cases = [
            (
                "/blog/for/J%C3%BCrgen%20M%C3%BCnster/",
                "/blog/for/J\xfcrgen%20M\xfcnster/",
            ),
            ("%&", "%&"),
            ("red&%E2%99%A5ros%#red", "red&♥ros%#red"),
            ("/%E2%99%A5%E2%99%A5/", "/♥♥/"),
            ("/%E2%99%A5%E2%99%A5/?utf8=%E2%9C%93", "/♥♥/?utf8=✓"),
            ("/%25%20%02%7b/", "/%25%20%02%7b/"),
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
                self.assertEqual(iri_to_uri(uri_to_iri(uri)), uri)
                self.assertEqual(uri_to_iri(iri_to_uri(iri)), iri)