def test_whitespace_in_route(self):
        msg = "URL route %r cannot contain whitespace in angle brackets <…>"
        for whitespace in string.whitespace:
            with self.subTest(repr(whitespace)):
                route = "space/<int:num>/extra/<str:%stest>" % whitespace
                with self.assertRaisesMessage(ImproperlyConfigured, msg % route):
                    path(route, empty_view)
        # Whitespaces are valid in paths.
        p = path("space%s/<int:num>/" % string.whitespace, empty_view)
        match = p.resolve("space%s/1/" % string.whitespace)
        self.assertEqual(match.kwargs, {"num": 1})