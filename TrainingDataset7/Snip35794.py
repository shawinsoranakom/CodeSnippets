def test_resolver_reverse(self):
        resolver = get_resolver("urlpatterns_reverse.named_urls")
        test_urls = [
            # (name, args, kwargs, expected)
            ("named-url1", (), {}, ""),
            ("named-url2", ("arg",), {}, "extra/arg/"),
            ("named-url2", (), {"extra": "arg"}, "extra/arg/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(resolver.reverse(name, *args, **kwargs), expected)