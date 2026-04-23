def test_loaders_dirs(self):
        engine = Engine(
            loaders=[("django.template.loaders.filesystem.Loader", [TEMPLATE_DIR])]
        )
        template = engine.get_template("index.html")
        self.assertEqual(template.origin.name, os.path.join(TEMPLATE_DIR, "index.html"))