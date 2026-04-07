def test_404_tried_urls_have_names(self):
        """
        The list of URLs that come back from a Resolver404 exception contains
        a list in the right format for printing out in the DEBUG 404 page with
        both the patterns and URL names, if available.
        """
        urls = "urlpatterns_reverse.named_urls"
        # this list matches the expected URL types and names returned when
        # you try to resolve a nonexistent URL in the first level of included
        # URLs in named_urls.py (e.g., '/included/nonexistent-url')
        url_types_names = [
            [{"type": URLPattern, "name": "named-url1"}],
            [{"type": URLPattern, "name": "named-url2"}],
            [{"type": URLPattern, "name": None}],
            [{"type": URLResolver}, {"type": URLPattern, "name": "named-url3"}],
            [{"type": URLResolver}, {"type": URLPattern, "name": "named-url4"}],
            [{"type": URLResolver}, {"type": URLPattern, "name": None}],
            [{"type": URLResolver}, {"type": URLResolver}],
        ]
        with self.assertRaisesMessage(Resolver404, "tried") as cm:
            resolve("/included/nonexistent-url", urlconf=urls)
        e = cm.exception
        # make sure we at least matched the root ('/') url resolver:
        self.assertIn("tried", e.args[0])
        self.assertEqual(
            len(e.args[0]["tried"]),
            len(url_types_names),
            "Wrong number of tried URLs returned. Expected %s, got %s."
            % (len(url_types_names), len(e.args[0]["tried"])),
        )
        for tried, expected in zip(e.args[0]["tried"], url_types_names):
            for t, e in zip(tried, expected):
                with self.subTest(t):
                    self.assertIsInstance(
                        t, e["type"]
                    ), "%s is not an instance of %s" % (t, e["type"])
                    if "name" in e:
                        if not e["name"]:
                            self.assertIsNone(
                                t.name, "Expected no URL name but found %s." % t.name
                            )
                        else:
                            self.assertEqual(
                                t.name,
                                e["name"],
                                'Wrong URL name. Expected "%s", got "%s".'
                                % (e["name"], t.name),
                            )