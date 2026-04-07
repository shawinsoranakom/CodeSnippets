def test_lazy_template_string(self):
        template_string = gettext_lazy("lazy string")
        self.assertEqual(Template(template_string).render(Context()), template_string)