def test_cached_exception_no_traceback(self):
        """
        When a TemplateDoesNotExist instance is cached, the cached instance
        should not contain the __traceback__, __context__, or __cause__
        attributes that Python sets when raising exceptions.
        """
        self.engine.debug = True
        with self.assertRaises(TemplateDoesNotExist):
            self.engine.get_template("no-traceback-in-cache.html")
        e = self.engine.template_loaders[0].get_template_cache[
            "no-traceback-in-cache.html"
        ]

        error_msg = "Cached TemplateDoesNotExist must not have been thrown."
        self.assertIsNone(e.__traceback__, error_msg)
        self.assertIsNone(e.__context__, error_msg)
        self.assertIsNone(e.__cause__, error_msg)