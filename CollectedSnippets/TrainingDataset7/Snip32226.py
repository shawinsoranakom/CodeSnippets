def test_get_protocol_defined_in_constructor(self):
        for protocol in ["http", "https"]:
            with self.subTest(protocol=protocol):
                sitemap = GenericSitemap({"queryset": None}, protocol=protocol)
                self.assertEqual(sitemap.get_protocol(), protocol)