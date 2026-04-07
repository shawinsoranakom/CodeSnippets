def test_match_lazy_route_without_converters(self):
        pattern = RoutePattern(_("test/"))
        result = pattern.match("test/child/")
        self.assertEqual(result, ("child/", (), {}))