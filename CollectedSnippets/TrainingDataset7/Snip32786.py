def test_select_template_first_engine(self):
        template = select_template(
            ["template_loader/unknown.html", "template_loader/hello.html"]
        )
        self.assertEqual(template.render(), "Hello! (template strings)\n")