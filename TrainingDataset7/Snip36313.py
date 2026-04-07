def test_get_tag_uri_with_port(self):
        """
        get_tag_uri() correctly generates TagURIs from URLs with port numbers.
        """
        self.assertEqual(
            feedgenerator.get_tag_uri(
                "http://www.example.org:8000/2008/11/14/django#headline",
                datetime.datetime(2008, 11, 14, 13, 37, 0),
            ),
            "tag:www.example.org,2008-11-14:/2008/11/14/django/headline",
        )