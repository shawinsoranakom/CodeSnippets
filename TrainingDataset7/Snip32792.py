def test_select_template_tries_all_engines_before_names(self):
        template = select_template(
            ["template_loader/goodbye.html", "template_loader/hello.html"]
        )
        self.assertEqual(template.render(), "Goodbye! (Django templates)\n")