def test_not_installed(self):
        with self.assertRaises(TemplateDoesNotExist):
            self.engine.get_template("index.html")