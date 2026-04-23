def test_get_protocol_default(self):
        sitemap = GenericSitemap({"queryset": None})
        self.assertEqual(sitemap.get_protocol(), "https")