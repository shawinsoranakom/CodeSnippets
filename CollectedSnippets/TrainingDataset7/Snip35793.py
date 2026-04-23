def test_reverse_lazy_object_coercion_by_resolve(self):
        """
        Verifies lazy object returned by reverse_lazy is coerced to
        text by resolve(). Previous to #21043, this would raise a TypeError.
        """
        urls = "urlpatterns_reverse.named_urls"
        proxy_url = reverse_lazy("named-url1", urlconf=urls)
        resolver = get_resolver(urls)
        resolver.resolve(proxy_url)