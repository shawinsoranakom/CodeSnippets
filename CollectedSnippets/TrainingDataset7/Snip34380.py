def test_template_name_lazy_string(self):
        """
        #26603 -- A template name specified as a lazy string should be forced
        to text before computing its cache key.
        """
        self.assertEqual(
            self.engine.template_loaders[0].cache_key(lazystr("template.html"), []),
            "template.html",
        )