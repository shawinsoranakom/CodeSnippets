def test_loaders_dirs_empty(self):
        """An empty dirs list in loaders overrides top level dirs."""
        engine = Engine(
            dirs=[TEMPLATE_DIR],
            loaders=[("django.template.loaders.filesystem.Loader", [])],
        )
        with self.assertRaises(TemplateDoesNotExist):
            engine.get_template("index.html")