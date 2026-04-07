def test_get_template_using_engine(self):
        template = get_template("template_loader/hello.html", using="django")
        self.assertEqual(template.render(), "Hello! (Django templates)\n")