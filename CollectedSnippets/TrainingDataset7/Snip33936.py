def test_querystring_non_mapping_args(self):
        cases = [None, 0, "", []]
        request = self.request_factory.get("/")
        msg = (
            "querystring requires mappings for positional arguments (got %r "
            "instead)."
        )
        for param in cases:
            with self.subTest(param=param):
                context = RequestContext(request, {"somevar": param})
                self.assertTemplateSyntaxError(
                    "querystring_non_mapping_args", context, msg % param
                )