def test_get_tag_uri(self):
        """
        get_tag_uri() correctly generates TagURIs.
        """
        self.assertEqual(
            feedgenerator.get_tag_uri(
                "http://example.org/foo/bar#headline", datetime.date(2004, 10, 25)
            ),
            "tag:example.org,2004-10-25:/foo/bar/headline",
        )