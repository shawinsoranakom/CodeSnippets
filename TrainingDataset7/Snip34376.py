def test_get_template_missing_debug_off(self):
        """
        With template debugging disabled, the raw TemplateDoesNotExist class
        should be cached when a template is missing. See ticket #26306 and
        docstrings in the cached loader for details.
        """
        self.engine.debug = False
        with self.assertRaises(TemplateDoesNotExist):
            self.engine.get_template("prod-template-missing.html")
        e = self.engine.template_loaders[0].get_template_cache[
            "prod-template-missing.html"
        ]
        self.assertEqual(e, TemplateDoesNotExist)