def test_loader_priority(self):
        """
        #21460 -- The order of template loader works.
        """
        loaders = [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ]
        engine = Engine(dirs=[OTHER_DIR, TEMPLATE_DIR], loaders=loaders)
        template = engine.get_template("priority/foo.html")
        self.assertEqual(template.render(Context()), "priority\n")