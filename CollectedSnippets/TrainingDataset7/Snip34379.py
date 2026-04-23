def test_template_name_leading_dash_caching(self):
        """
        #26536 -- A leading dash in a template name shouldn't be stripped
        from its cache key.
        """
        self.assertEqual(
            self.engine.template_loaders[0].cache_key("-template.html", []),
            "-template.html",
        )