def test_match_lazy_route_endpoint(self):
        pattern = RoutePattern(_("test/"), is_endpoint=True)
        result = pattern.match("test/")
        self.assertEqual(result, ("", (), {}))