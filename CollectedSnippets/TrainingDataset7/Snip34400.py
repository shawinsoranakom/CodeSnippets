def test_get_template(self):
        template = self.engine.get_template("index.html")
        self.assertEqual(template.origin.name, "index.html")
        self.assertEqual(template.origin.template_name, "index.html")
        self.assertEqual(template.origin.loader, self.engine.template_loaders[0])