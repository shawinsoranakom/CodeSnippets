def test_resolver_reverse_conflict(self):
        """
        URL pattern name arguments don't need to be unique. The last registered
        pattern takes precedence for conflicting names.
        """
        resolver = get_resolver("urlpatterns_reverse.named_urls_conflict")
        test_urls = [
            # (name, args, kwargs, expected)
            # Without arguments, the last URL in urlpatterns has precedence.
            ("name-conflict", (), {}, "conflict/"),
            # With an arg, the last URL in urlpatterns has precedence.
            ("name-conflict", ("arg",), {}, "conflict-last/arg/"),
            # With a kwarg, other URL patterns can be reversed.
            ("name-conflict", (), {"first": "arg"}, "conflict-first/arg/"),
            ("name-conflict", (), {"middle": "arg"}, "conflict-middle/arg/"),
            ("name-conflict", (), {"last": "arg"}, "conflict-last/arg/"),
            # The number and order of the arguments don't interfere with
            # reversing.
            ("name-conflict", ("arg", "arg"), {}, "conflict/arg/arg/"),
        ]
        for name, args, kwargs, expected in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                self.assertEqual(resolver.reverse(name, *args, **kwargs), expected)