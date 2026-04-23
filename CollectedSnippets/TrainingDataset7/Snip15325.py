def test_parse_rst(self):
        """
        parse_rst() should use `cmsreference` as the default role.
        """
        markup = '<p><a class="reference external" href="/admindocs/%s">title</a></p>\n'
        self.assertEqual(parse_rst("`title`", "model"), markup % "models/title/")
        self.assertEqual(parse_rst("`title`", "view"), markup % "views/title/")
        self.assertEqual(parse_rst("`title`", "template"), markup % "templates/title/")
        self.assertEqual(parse_rst("`title`", "filter"), markup % "filters/#title")
        self.assertEqual(parse_rst("`title`", "tag"), markup % "tags/#title")