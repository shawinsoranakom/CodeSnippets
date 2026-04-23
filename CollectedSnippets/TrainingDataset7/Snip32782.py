def test_get_template_first_engine(self):
        template = get_template("template_loader/hello.html")
        self.assertEqual(template.render(), "Hello! (template strings)\n")