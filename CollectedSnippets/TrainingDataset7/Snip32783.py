def test_get_template_second_engine(self):
        template = get_template("template_loader/goodbye.html")
        self.assertEqual(template.render(), "Goodbye! (Django templates)\n")