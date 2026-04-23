def test_get_template_missing_debug_on(self):
        """
        With template debugging enabled, a TemplateDoesNotExist instance
        should be cached when a template is missing.
        """
        self.engine.debug = True
        with self.assertRaises(TemplateDoesNotExist):
            self.engine.get_template("debug-template-missing.html")
        e = self.engine.template_loaders[0].get_template_cache[
            "debug-template-missing.html"
        ]
        self.assertIsInstance(e, TemplateDoesNotExist)
        self.assertEqual(e.args[0], "debug-template-missing.html")