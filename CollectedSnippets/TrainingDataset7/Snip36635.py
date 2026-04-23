def test_mark_safe_lazy_i18n(self):
        s = mark_safe(gettext_lazy("name"))
        tpl = Template("{{ s }}")
        with translation.override("fr"):
            self.assertEqual(tpl.render(Context({"s": s})), "nom")