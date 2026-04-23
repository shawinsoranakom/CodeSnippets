def test_get_protocol_passed_as_argument(self):
        sitemap = GenericSitemap({"queryset": None})
        for protocol in ["http", "https"]:
            with self.subTest(protocol=protocol):
                self.assertEqual(sitemap.get_protocol(protocol), protocol)