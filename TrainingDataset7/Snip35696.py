def test_has_converters(self):
        self.assertEqual(len(RoutePattern("translated/").converters), 0)
        self.assertEqual(len(RoutePattern(_("translated/")).converters), 0)
        self.assertEqual(len(RoutePattern("translated/<int:foo>").converters), 1)
        self.assertEqual(len(RoutePattern(_("translated/<int:foo>")).converters), 1)