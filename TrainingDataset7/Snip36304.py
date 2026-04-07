def test_iri_to_uri(self):
        cases = [
            # Valid UTF-8 sequences are encoded.
            ("red%09rosé#red", "red%09ros%C3%A9#red"),
            ("/blog/for/Jürgen Münster/", "/blog/for/J%C3%BCrgen%20M%C3%BCnster/"),
            (
                "locations/%s" % quote_plus("Paris & Orléans"),
                "locations/Paris+%26+Orl%C3%A9ans",
            ),
            # Reserved chars remain unescaped.
            ("%&", "%&"),
            ("red&♥ros%#red", "red&%E2%99%A5ros%#red"),
            (gettext_lazy("red&♥ros%#red"), "red&%E2%99%A5ros%#red"),
        ]

        for iri, uri in cases:
            with self.subTest(iri):
                self.assertEqual(iri_to_uri(iri), uri)

                # Test idempotency.
                self.assertEqual(iri_to_uri(iri_to_uri(iri)), uri)