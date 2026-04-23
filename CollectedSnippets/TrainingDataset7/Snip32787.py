def test_select_template_second_engine(self):
        template = select_template(
            ["template_loader/unknown.html", "template_loader/goodbye.html"]
        )
        self.assertEqual(template.render(), "Goodbye! (Django templates)\n")