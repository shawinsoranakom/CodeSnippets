def test_match_lazy_route_with_converters(self):
        pattern = RoutePattern(_("test/<int:pk>/"))
        result = pattern.match("test/123/child/")
        self.assertEqual(result, ("child/", (), {"pk": 123}))