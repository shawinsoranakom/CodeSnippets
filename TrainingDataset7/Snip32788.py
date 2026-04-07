def test_select_template_using_engine(self):
        template = select_template(
            ["template_loader/unknown.html", "template_loader/hello.html"],
            using="django",
        )
        self.assertEqual(template.render(), "Hello! (Django templates)\n")