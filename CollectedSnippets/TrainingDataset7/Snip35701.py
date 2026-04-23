def test_lazy_route_resolves(self):
        resolver = get_resolver("urlpatterns.lazy_path_urls")
        for url_path, name in [
            ("/lazy/test-me/", "lazy"),
            ("/included_urls/extra/test/", "inner-extra"),
        ]:
            with self.subTest(name=name):
                match = resolver.resolve(url_path)
                self.assertEqual(match.func, views.empty_view)
                self.assertEqual(match.url_name, name)