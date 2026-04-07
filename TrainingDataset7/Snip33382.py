def test_multiple_locale_loadi18n_deactivate(self):
        with translation.override("de", deactivate=True):
            t = Template("{% load i18n %}{{ _('No') }}")
        with translation.override("nl"):
            self.assertEqual(t.render(Context({})), "Nee")