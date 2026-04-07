def test_ambiguous_urlpattern(self):
        """
        Names deployed via dynamic URL objects that require namespaces can't
        be resolved.
        """
        test_urls = [
            ("inner-nothing", [], {}),
            ("inner-nothing", [37, 42], {}),
            ("inner-nothing", [], {"arg1": 42, "arg2": 37}),
        ]
        for name, args, kwargs in test_urls:
            with self.subTest(name=name, args=args, kwargs=kwargs):
                with self.assertRaises(NoReverseMatch):
                    reverse(name, args=args, kwargs=kwargs)