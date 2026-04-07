def test_multiple_locale_loadi18n(self):
        with translation.override("de"):
            t = Template("{% load i18n %}{{ _('No') }}")
        with translation.override(self._old_language), translation.override("nl"):
            self.assertEqual(t.render(Context({})), "Nee")